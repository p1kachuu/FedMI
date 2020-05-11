# -*- coding: UTF-8 -*-
""" 
paillier enctyption, decryption algorithm based on key division
provid some functions to encrype and decrypt
"""

import math
import random

def encrypt(m, pk, bitLength=1024):
    if not isinstance(m, int):
        raise ValueError("only support integer!")
    n = pk
    n_square = pow(n,2)
    beta = random.randrange(0, 2**bitLength)
    c = (1 + m*n) * (pow(beta, n, n_square))
    return c

def decrypt(c, pk, sk):
    n = pk
    n_square = pow(n, 2)
    lambdaa = sk
    m = (pow(c, sk, n_square) - 1) // n
    #modInverse ns or n
    invLamda = inv_mod(lambdaa, n)
    res = m * invLamda % n
    return res

def inv_mod(val, n):
    if(math.gcd(n,val)>1):
        raise ArithmeticError("modulus and this have commen dividor >1 ")
    res = ext_euclid(val, n)
    return res[0]

def ext_euclid(val, mod):
    res = []
    if(mod == 0):
        res.append(1)
        res.append(0)
        res.append(val)
        return res
    else :
        temp = ext_euclid(mod, val % mod)
        res.append(temp[1])
        res.append(temp[0]-temp[1]*(val//mod))
        res.append(temp[2])
    return res

def share_dec(c, pk, ski):
    n_square = pow(pk, 2)
    return pow(c, ski, n_square)

def dec_with_shares(sdec1, sdec2, pk):
    n_square = pow(pk, 2)
    c = sdec1 * sdec2
    res = (c % n_square - 1) // pk
    if(res>pk/2):
        res = res - pk
    return res
    