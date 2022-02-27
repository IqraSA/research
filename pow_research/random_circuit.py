import random

modulus = 97

def mkrandom(width, length):
    return [(random.randrange(width), random.randrange(width),
                 random.randrange(width)) for _ in range(length)]

def eval(inp, prog):
    o = list(inp)
    for p in prog:
        out, mul1, mul2 = p
        o[out] = (o[out] + mul1 * mul2) % modulus
    return o

def mkinp(width):
    return [random.randrange(modulus) for _ in range(width)]
