# -*- encoding: utf-8 -*-
# Obiekty do przesyłania przez sieć

class Position(object):
    def __init__(self, y, x):
        self.y = y
        self.x = x

    def __str__(self):
        return "(%d, %d)" % (self.y, self.x)

    def __eq__(self, other):
        return self.y == other.y and self.x == other.x

class Mine(object):
    def __init__(self, position, playerId):
        self.position = position
        self.playerId = playerId

class Countdown(object):
    def __init__(self, number, mapSize, playerId):
        self.number = number
        self.mapSize = mapSize
        self.playerId = playerId

class Map(object):
    def __init__(self, mines, playersPositions):
        self.mines = mines
        self.playersPositions = playersPositions

class PlayerAction(object):
    def __init__(self, action):
        self.action = action

class Result(object):
    def __init__(self, winners, scores):
        self.winners = winners
        self.scores = scores

# DODATKOWE WEWNĘTRZNE DLA SERWERA
class Player(object):
    def __init__(self, _id, (x, y), client):
        self.id = _id
        self.alive = True
        self.position = Position(y, x)
        self.client = client

    def move(self, (dx, dy)):
        if self.client.factory.movePlayer(self.id, (self.position.x - 1, self.position.y - 1), (self.position.x + dx - 1, self.position.y + dy - 1)):
            self.position.x += dx
            self.position.y += dy
            self.alive = not self.client.factory.getMine((self.position.x - 1, self.position.y - 1))

    def putMine(self):
        return self.client.factory.putMine(self.id, self.position)
