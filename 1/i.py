pExact = .8
pOver = .1
pUnder = .1
p = [0, .5, 0, .5, 0]
def move(p, U):
    _len = len(p)
    return [p[(i - U) % _len] * pExact +
            p[(i - U - 1) % _len] * pOver +
            p[(i - U + 1) % _len] * pUnder
            for i in range(_len)]

if __name__ == '__main__':
    for _ in range(1000):
        p = move(p, 2)

    print(p)
