N = 5
p = [1./N] * N

pHit = 0.6
pMiss = 0.2

world = ['green', 'red', 'red', 'green', 'green']

def sense(p, Z):
    q = [l * (z == Z and pHit or pMiss) for z, l in zip(world, p)]
    s = sum(q)
    return list(map(lambda x: x/s, q))

if __name__ == '__main__':
    print(p)
    print('R:', sense(p, 'red'))
    print('G:', sense(p, 'green'))
