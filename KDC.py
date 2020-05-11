# -*- coding: UTF-8 -*-
# paillier key distribution server based on key splitting
from Paillier import Paillier
import hmac
import os
import time
import socket
import sys
import pickle
import struct
import threading 

hamc_secret_key = b'boyun'
kdc_info = ('127.0.0.1', 10001)
server_info = ('127.0.0.1', 9998) # 服务器接收客户端密钥信息

def server_authenticate(conn, secret_key):
    '''
    Request client authentication.
    '''
    message = os.urandom(32)
    conn.send(message)
    hash = hmac.new(secret_key, message)
    digest = hash.digest()
    response = conn.recv(len(digest))
    return hmac.compare_digest(digest, response)

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
    
def handler(conn, addr):
    if not server_authenticate(conn, hamc_secret_key):
        # conn.send("authentication failed! ".encode())
        send_data(conn, "authentication failed! ")
        conn.close
    else:
        print("**********************{}****************************".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        print("[INFO] successful authentication from {}:{}".format(addr[0], addr[1]))
        # conn.send("authentication success!".encode())
        send_data(conn, "authentication success!")
        # receive cid, client_ip
        # cid = conn.recv(128).decode(encoding='utf-8')
        # client_ip = conn.recv(128).decode(encoding='utf-8')
        cid = recv_data(conn)
        client_ip = recv_data(conn)
        # if authentication success, split secret key to p0, p1, 
        # one send to server, another to client
        p0, p1 = paillier_sys.key_splitting()
        # send to client
        print("[INFO] sending key to client_{}:{}".format(cid, addr))
        # conn.sendall(str(pk).encode(encoding='utf-8'))
        # conn.sendall(str(p1).encode(encoding='utf-8'))
        send_data(conn, str(pk))
        send_data(conn, str(p1))
        # send to server
        sock_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_to_server.connect(server_info)
        print("[INFO] sending key to server")
        # sock_to_server.send(str(cid).encode(encoding='utf-8'))
        # sock_to_server.send(str(client_ip).encode(encoding='utf-8'))
        # sock_to_server.send(str(pk).encode(encoding='utf-8'))
        # sock_to_server.send(str(p0).encode(encoding='utf-8'))
        send_data(sock_to_server, cid)
        send_data(sock_to_server, client_ip)
        send_data(sock_to_server, str(pk))
        send_data(sock_to_server, str(p0))
        isupdated = recv_data(sock_to_server)
        if(isupdated==1):
            print("[INFO] updating database is ok!")
        # bug?
        send_data(conn, isupdated)
        sock_to_server.close()
        conn.close()

# create paillier system
paillier_sys = Paillier()
pk = paillier_sys.n 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(kdc_info)
s.listen(5)

print('KDC:启动socket服务，等待客户端连接...')
while True:
    conn, addr = s.accept()
    t = threading.Thread(target=handler, args=(conn, addr))
    t.start()