# -*- coding: UTF-8 -*-
""" 接受来自KDC的各个客户端的部分私钥将其存储到MySql中 """
import mysql.connector
import socket
import sys
import pickle
import struct
import time
import threading

# mysql配置信息
config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'port': 3306,
    'database': 'ClientDB',
    'charset': 'utf8'
}
kdc_info = "127.0.0.1" 
key_sever_info = ('127.0.0.1',9998)

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

def handler(conn, config):
    # cid = conn.recv(128).decode(encoding='utf-8')
    # client_ip = conn.recv(128).decode(encoding='utf-8')
    # pk = conn.recv(1024).decode(encoding='utf-8')
    # sk0 = conn.recv(1024).decode(encoding='utf-8')
    print("**********************{}****************************".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    cid = recv_data(conn)
    client_ip = recv_data(conn)
    pk = recv_data(conn)
    sk0 = recv_data(conn)
    print("[cid]", cid)
    print("[client ip]", client_ip)
    print("[pk]", pk)
    print("[sk0]", sk0)
    print("[info] received client_%d\'s msg, ip is %s" % (cid, client_ip))
    lock.acquire()
    # sql插入client信息, 如果存在对应的cid则更新，如果不存在则创建
    # sql = """INSERT INTO `client_info`(
    #     cid, ip, public_key, sk0, isTrainable)
    #     VALUES(
    #         {0}, "{1}", "{2}", "{3}", 1)
    #     ON DUPLICATE KEY UPDATE
    #         cid = {0}, ip = "{1}", public_key = "{2}", sk0 = "{3}", isTrainable = 1;
    # """ .format(cid, client_ip, pk, sk0)
    sql = "UPDATE `client_info` SET `ip` = '{1}', `public_key` = '{2}', `sk0` = '{3}', `isTrainable` = 1 WHERE `client_info`.`cid` = {0}".format(cid, client_ip, pk, sk0)
    print("[info] updating database...")
    db = conndb(config)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    lock.release()
    send_data(conn, 1)
    conn.close()
    db.close()
    
lock = threading.Lock() # threading lock
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(key_sever_info)
s.listen(5)

print('receiving paillier key part from KDC...')
while True:
    conn, addr = s.accept()
    if(addr[0] != kdc_info):
        print('receive unknown server info!')
        continue
    t = threading.Thread(target=handler, args=(conn,config))
    t.start()