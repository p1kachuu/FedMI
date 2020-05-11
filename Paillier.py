# -*- coding: UTF-8 -*-
""" 
paillier enctyption, decryption algorithm based on key division
complete system used for kdc
"""
import math
import random
from phe.util import getprimeover

class Paillier:
    def __init__(self, bit_length=1024):
        self.bit_length = bit_length
        self.n, self.lambdaa = self.generate_paillier_key(bit_length)
        self.nsquare = pow(self.n,2)

    def enctypt(self, m):
        if not isinstance(m, int):
            raise ValueError("only support integer!")
        n = self.n
        nsquare = self.nsquare
        beta = random.randrange(0, 2**self.bit_length)
        c = (1 + m*n) * (pow(beta, n, nsquare))
        return c

    def decrypt(self, c):
        n = self.n
        nsquare = self.nsquare
        sk = self.lambdaa
        m = (pow(c, sk, nsquare) - 1) // n
        #modInverse ns or n
        invLamda = self.inv_mod(sk, n) 
        res = m * invLamda % n
        if(res>n/2):
            res = res - n
        return res

    def inv_mod(self, val, n):
        if(math.gcd(n,val)>1):
            raise ArithmeticError("modulus and this have commen dividor >1 ")
        res = self.ext_euclid(val, n)
        return res[0]
            
    def ext_euclid(self, val, mod):
        res = []
        if(mod == 0):
            res.append(1)
            res.append(0)
            res.append(val)
            return res
        else :
            temp = self.ext_euclid(mod, val % mod)
            res.append(temp[1])
            res.append(temp[0]-temp[1]*(val//mod))
            res.append(temp[2])
        return res
        
    def key_splitting(self):
        nsquare = self.nsquare
        lambdaa = self.lambdaa
        kk1 = lambdaa * nsquare
        kkk = findModReverse(lambdaa, nsquare)
        s = lambdaa * kkk % kk1
        p0 = random.randrange(0, 2**self.bit_length)
        p1 = s - p0
        return p0, p1

    def share_dec(self, c, ski):
        pk = self.n
        nsquare = pow(pk, 2)
        return pow(c, ski, nsquare)
    
    def dec_with_shares(self, sdec1, sdec2):
        pk = self.n
        nsquare = pow(pk, 2)
        c = sdec1 * sdec2
        res = (c % nsquare - 1) // pk
        if(res>pk/2):
            res = res - pk
        return res

    def generate_paillier_key(self, n_length):
        p = q = n = None
        g = 2 
        n_len = 0
        while n_len != n_length:
            p = getprimeover(n_length // 2)
            q = getprimeover(n_length // 2)
            n = p * q
            n_len = n.bit_length()
        lambdaa = (p-1)*(q-1) // math.gcd(p-1, q-1)
        # check whether g is good. 
        temp = (pow(g, lambdaa, n**2) - 1) // n
        if(math.gcd(temp, n) != 1):
             raise ArithmeticError("g is not good. Choose g again.")
        return n, lambdaa

def findModReverse(a,m):    # 扩展欧几里得算法求模逆
    if math.gcd(a,m)!=1:
        return None
    u1, u2, u3 = 1, 0, a
    v1, v2, v3 = 0, 1, m
    while v3 != 0:
        q = u3//v3
        v1, v2, v3, u1, u2, u3 = (u1-q*v1), (u2-q*v2), (u3-q*v3), v1, v2, v3
    return u1 % m