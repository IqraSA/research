#from Crypto.Hash import SHA256
from binascii import hexlify
import random, hashlib


def normal_distribution(mean, standev):
    def f():
        return int(random.normalvariate(mean, standev))

    return f


def exponential_distribution(mean):
    def f():
        total = 0
        while 1:
            total += 1
            if not random.randrange(32):
                break
        return int(total * 0.03125 * mean)

    return f


def convolve(*args):
    def f():
        return sum(arg() for arg in args)

    return f


def transform(dist, xformer):
    def f():
        return xformer(dist())

    return f


def to_hex(s):
    return hexlify(s).decode('utf-8')

memo = {}

#def sha3(x):
#    if x not in memo:
#        memo[x] = SHA256.new(data=x).digest()
#    return memo[x]


def sha3(x):
    if x not in memo:
        m = hashlib.sha256(x)
        memo[x] = m.digest()
    return memo[x]

def hash_to_int(h):
    o = 0
    for c in h:
        if type(c).__name__ != 'int' : # This is necessary for Python2
            c = ord(c)
        o = (o << 8) + c
    return o


def checkpow(work, nonce, powdiff):
    # Discrete log PoW, lolz
    # Quadratic nonresidues only
    return pow(work, nonce, 65537) * powdiff < 65537 * 2 and pow(nonce, 32768, 65537) == 65536

