N = 5
p = [1./N]*N

world = ['green', 'red', 'red', 'green', 'green']
measurements = ['red', 'green']

pHit = 0.6
pMiss = 0.2

def sense(p, Z):
    q = [l * (z == Z and pHit or pMiss) for z, l in zip(world, p)]
    s = sum(q)
    return list(map(lambda x: x/s, q))

if __name__ == '__main__':
    for measurement in measurements:
        p = sense(p, measurement)
        print(measurement+'>', p)
