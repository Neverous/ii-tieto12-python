N = 5
p = [1./N] * N

pHit = 0.6
pMiss = 0.2

if __name__ == '__main__':
    for m in (0, 3, 4):
        p[m] *= pMiss

    for h in (1, 2):
        p[h] *= pHit

    print(p)
