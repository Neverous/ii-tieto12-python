N = 5
p = [1./N]*N

world = ['green', 'red', 'red', 'green', 'green']
measurements = ['red', 'green', 'red', 'red', 'red', 'red', 'red', 'green', 'red']
motions = [1, -2, 0, 1, 0, 0, 1, -1, 0]

pHit = 0.6
pMiss = 0.2
pExact = .8
pOver = .1
pUnder = .1

def move(p, U):
    _len = len(p)
    return [p[(i - U) % _len] * pExact +
            p[(i - U - 1) % _len] * pOver +
            p[(i - U + 1) % _len] * pUnder
            for i in range(_len)]

def sense(p, Z):
    q = [l * (z == Z and pHit or pMiss) for z, l in zip(world, p)]
    s = sum(q)
    return list(map(lambda x: x/s, q))

if __name__ == '__main__':
    for mea, mot in zip(measurements, motions):
        p = sense(p, mea)
        print(p)
        p = move(p, mot)
        print(p)
        print('')
