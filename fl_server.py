# -*- coding: UTF-8 -*-
import socket
import pickle
import struct
import sys
import time
import numpy as np 
import threading
import mysql.connector

server_info = ('127.0.0.1', 9999) # server ip:port
client_weights_sum = 1
epochs = 5
# global_weights = None # global weights

#### SOME TRAINING PARAMS ####
# mysql配置信息
config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'port': 3306,
    'database': 'ClientDB',
    'charset': 'utf8'
}

def conndb(config):
    ''' connect database '''
    try:
        cnx = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
    return cnx

def send_data(conn, data):
    """ This function used to send data with sock """
    # serialize data
    msg = pickle.dumps(data, protocol=0)
    # size of msg
    size = sys.getsizeof(msg)
    header = struct.pack("i", size)
    # send header
    conn.sendall(header)
    # send msg
    conn.sendall(msg)

def recv_data(conn):
    """ This function used to recvive data with sock """
    # receive header and unpack
    header = conn.recv(4)
    size = struct.unpack('i', header)
    # receive msg
    recv_msg = b""
    while(sys.getsizeof(recv_msg)<size[0]):
        recv_msg += conn.recv(size[0]-sys.getsizeof(recv_msg))
    data = pickle.loads(recv_msg)
    return data

def share_dec(c, pk, ski):
    n_square = pow(pk, 2)
    return pow(c, ski, n_square)

def get_clients_params(conn):
    """ get clients weights """
    # header = conn.recv(4)
    # size = struct.unpack('i', header)
    # # receive data
    # recv_data = b""
    # while(sys.getsizeof(recv_data)<size[0]):
    #     recv_data += conn.recv(size[0]) 
    # # unserialize data
    # data = pickle.loads(recv_data)
    data = recv_data(conn)
    return data

def send_global_params(global_weights, c0, conn):
    """ send global weights to clients """
    # serialize data
    # data_weights = pickle.dumps(global_weights, protocol=0)
    # data_c0 = pickle.dumps(c0, protocol=0)
    # # size of data
    # size_weights = sys.getsizeof(data_weights)
    # size_c0 = sys.getsizeof(data_c0)
    # #print("data size:", size)
    # header_weights = sys.getsizeof("i", size_weights)
    # header_c0 = struct.pack("i", size_c0)
    # print("sending global params!")
    # # send weights
    # conn.sendall(header_weights)
    # conn.sendall(data_weights)
    # # send c0
    # conn.sendall(header_c0)
    # conn.sendall(data_c0)
    send_data(conn, global_weights)
    send_data(conn, c0)

def thread_handler(conn, cid, epoch, epochs):
    """ thread handler to get clients weights """
    global client_weights_list
    global client_weights_sum
    pk = int(clients_info[cid][1])
    sk0 = int(clients_info[cid][2])
    nsqure = pk**2
    c0_params = []
    if(epoch > 0):
        print("[INFO] calculating client_{}\'s c0_params".format(cid))
        for i in range(len(client_weights_sum)):
            shape = client_weights_sum[i].shape
            temp_arr = np.array([share_dec(int(x), pk, sk0) for x in np.nditer(client_weights_sum[i], flags=['refs_ok'])])
            c0_params.append(temp_arr.reshape(shape))
        print("[INFO] sending global weights and c0_params to client_{}...".format(cid))
        send_global_params(client_weights_sum, c0_params, conn)
    print("[INFO] waiting client_{} train...".format(cid))
    if(epoch < epochs-1):
        current_client_weights = get_clients_params(conn)
        print("[INFO] has get client_{}\'s weights..".format(cid))
        # append client weights to list
        client_weights_list.append(current_client_weights)
        condition_lock.acquire()
        if(len(client_weights_list)<client_num):
            condition_lock.wait()
        else:
            assert len(client_weights_list)==client_num  
            print("[INFO] calculating global weights..")
            # obtain global weights
            client_weights_sum = 1
            for i in range(client_num):
                client_weights_sum = (client_weights_sum * client_weights_list[i]) % nsqure
            # global_weights = client_weights_sum / client_num
            condition_lock.notify_all()
        condition_lock.release()
    conn.close()

# 从mysql数据库中读取client信息
cliendb = conndb(config)
query = "SELECT * FROM `client_info` WHERE isTrainable = 1"
cmd = cliendb.cursor()
cmd.execute(query)
res = cmd.fetchall()
cliendb.close()
# print(res)
client_num = len(res)
if(client_num==0):
    print("[Error] number of trainable clients is zero!")
    exit(1)
clients_info = {}
# for i in res:
#     clients_info[i[0]] = (i[1], i[2], i[3])

condition_lock = threading.Condition() # condition lock
# new a socket object and keep listening
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(server_info)
s.listen(5)

# start train 
for epoch in range(epochs):
    now = time.strftime("%b %d %H:%M:%S", time.localtime())
    print("{}------{}/{} epoch start-------------------------".format(now, epoch+1, epochs))
    client_weights_list = []    # all clients weights
    
    for i in range(client_num):  # get clients weights 
        # create connection
        conn, addr = s.accept()
        # receive client id and return client num 
        # cid = conn.recv(32).decode(encoding='utf-8')
        # conn.send(str(client_num).encode(encoding='utf-8'))
        cid = recv_data(conn)
        print ('[INFO] Connected by client_{}:{}'.format(cid, addr))
        send_data(conn, client_num)
        # connect mysql to query clients information
        query = """SELECT ip, public_key, sk0 FROM `client_info` 
                        WHERE cid = %d AND public_key IS NOT NULL AND sk0 IS NOT NULL""" %(cid)
        cliendb = conndb(config)
        cmd = cliendb.cursor()
        cmd.execute(query)
        res = cmd.fetchall()
        cliendb.close()
        if(len(res)==0):
            print("[Error] client_%d\'s public_key or sk0 is NULL!" %(cid))
            client_num = client_num - 1
            continue
        else:
            clients_info[cid] = (res[0][0], res[0][1], res[0][2])
        locals()["t"+str(i)] = threading.Thread(target=thread_handler, args=(conn, cid, epoch, epochs))
        locals()["t"+str(i)].start()

    for i in range(client_num):   # block main thread until all threads finish
        locals()["t"+str(i)].join()
    now = time.strftime("%b %d %H:%M:%S", time.localtime())
    print("{}------{}/{} epoch done-------------------------".format(now, epoch+1, epochs))
print("Federated learning done!")