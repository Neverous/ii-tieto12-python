pExact = .8
pOver = .1
pUnder = .1
p = [0, 0, 0, 0, 1]
def move(p, U):
    _len = len(p)
    return [p[(i - U) % _len] * pExact +
            p[(i - U - 1) % _len] * pOver +
            p[(i - U + 1) % _len] * pUnder
            for i in range(_len)]

if __name__ == '__main__':
    for i in range(-6, 7):
        print(i, move(p, i))
