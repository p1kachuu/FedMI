# -*- coding: UTF-8 -*-
import numpy as np 
import pickle, struct
import sys
import time
import hmac
import socket
from phe import paillier
from Client import Client

def client_authenticate(connection, secret_key):
    '''
    Authenticate client to a remote service.
    connection represents a network connection.
    secret_key is a key known only to both client/server.
    '''
    message = connection.recv(32)
    hash = hmac.new(secret_key, message)
    digest = hash.digest()
    connection.sendall(digest)

def get_paillier_keypair(server_info, client):
    """ get pailler keypair from KDC """
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(kdc_info)
    client_authenticate(conn, hamc_secret_key)
    # msg = conn.recv(100)
    # msg = msg.decode()
    msg = recv_data(conn)
    print('[INFO] client_{}:'.format(client_id) + msg)
    if(msg == 'authentication failed!'):
        conn.close()
        exit()
    # conn.send(str(client.cid).encode(encoding='utf-8'))
    # conn.send(str(client.ip).encode(encoding='utf-8'))
    send_data(conn, client.cid)
    send_data(conn, client.ip)
    # get paillier key
    print("[INFO] client_{}:get paillier key...".format(client_id))
    # pk = int(conn.recv(1024).decode(encoding='utf-8'))
    # sk1 = int(conn.recv(1024).decode(encoding='utf-8'))
    pk = int(recv_data(conn)) 
    sk1 = int(recv_data(conn))
    if(recv_data(conn)==1):
        print("[INFO] sever has updated database!")
    conn.close()
    return pk, sk1

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

def send_client_params(cipher, sock):
    """  Send client weights to server """
    print("[INFO] client_{}:sending cipher to server...".format(client_id))
    send_data(sock, cipher)
    
def load_global_params(sock):
    """ load encrypted global weights """
    print("[INFO] client_{}:loading weights...".format(client_id))
    # header_weights = sock.recv(4)
    # size_weights = struct.unpack('i', header_weights)
    # # receive data
    # recv_weights = b""
    # while(sys.getsizeof(recv_weights)<size_weights[0]):
    #     recv_weights += sock.recv(size_weights[0])
    # recv_c0 = b""
    # header_c0 = sock.recv(4)
    # size_c0 = struct.unpack('i', header_c0)
    # while(sys.getsizeof(recv_c0)<size_c0[0]):
    #     recv_c0 += sock.recv(size_c0[0])
    # # unserialize data 
    # data_weights = pickle.loads(recv_weights)
    # data_c0 = pickle.loads(recv_c0)
    data_weights = recv_data(sock)
    data_c0 = recv_data(sock)
    return data_weights, data_c0

# server msg
hamc_secret_key = b'boyun'
# server_info = ('47.93.194.45',9999)
# kdc_info = ('47.93.194.45', 10001)
server_info = ('127.0.0.1',9999)
kdc_info = ('127.0.0.1', 10001)

# new a client
epochs = 5
init_lr = 1e-3
datapath = './dataset'
client_id = 1001
client_ip = '127.0.0.1'
client = Client(init_lr, client_id, client_ip)

# get pk, sk from KDC
pk, sk1 = get_paillier_keypair(kdc_info, client)

# pk = 106504846927713258539210316352790353882162270818938504115679857002260675662663868186195764884050680158387910786319360594118394158988265190760518018383856211127828957901489657873023505978079816086418739645927283447419458899692329924108808874227987115411899682260014549514951147887170486841798910991527563787031
# sk1 = 54855930201116632641914550201734837220485525426007065029466442940440673772419705970813895348208263159742688478459129247731713857177365553634825552276367324516346187031786306150802038434735290492339330384379801798027124569500779162307451089750093030627109298663414427445131497800085849749634024347358542372461
print("[INFO] success get pk, sk")
epoch = 5

# start train
for epoch in range(epochs):
    now = time.strftime("%b %d %H:%M:%S", time.localtime())
    print("{}------client_{}:{}/{} epoch start-------------------------".format(now, client_id,epoch+1, epochs))
    # new a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind((client_ip, 9999))
    sock.connect(server_info)
    print("[INFO] client_{}:connect to {} ...".format(client_id, server_info))
    # send client id and receive number of clients
    # sock.send(str(client_id).encode(encoding='utf-8'))
    # client_num = sock.recv(32).decode(encoding='utf-8')
    send_data(sock, client_id)
    client_num = recv_data(sock)
    if(epoch > 0):
        # load global weights
        en_params, c0_params = load_global_params(sock)
        # decrypt weights
        de_global_weights = client.decrypt_global_weights_with_key_div(c0_params,en_params, sk1, pk)
        global_weights = np.array(de_global_weights) / client_num
        # set global weights
        client.set_weights(global_weights)
    # start tarin
    print("[INFO] client_{}:start train...".format(client_id))
    client.train_epoch()
    if(epoch < epochs-1):
        # get client weights
        client_weights = client.get_weights()
        # encrypt client weights
        en_client_weights = client.encrypt_weights_with_key_div(client_weights, pk)  
        # send encrypted weights
        send_client_params(en_client_weights, sock)
    sock.close()
    now = time.strftime("%b %d %H:%M:%S", time.localtime())
    print("{}------client_{}:{}/{} epoch done-------------------------".format(now, client_id, epoch+1, epochs))
# finall test
client.test_model()
client.plot_history("./en_fl_10_epoch.png")
# client.save_model("./model/covid19_VGG16.h5")
