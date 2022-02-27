import math
BLKTIME = 17
X = 0.28

faclog = [1]
faclog.extend(faclog[-1] * len(faclog) for _ in range(5000))

def fac(x):
    return faclog[x]

def poisson(expected, actual):
    if expected == 0:
        return 1 if actual == 0 else 0
    return 2.718281828 ** (-expected + actual * math.log(expected) - math.log(fac(actual)))

def p_we_win(k, x):
    return 1 - (x / (1.0 - x)) ** k

def p_we_win_after(s):
    return sum(poisson(s * 1.0 / BLKTIME, i) * p_we_win(i, X) for i in range(4000))

for i in range(0, 7200, 12):
    print i, p_we_win_after(i)
