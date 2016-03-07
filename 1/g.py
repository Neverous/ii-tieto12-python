def move(p, U):
    U %= len(p)
    return list(p[-U:]) + list(p[:-U])

if __name__ == '__main__':
    p = range(5)
    for i in range(-6, 7):
        print(i, move(p, i))
