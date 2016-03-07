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
    def __init__(self, _id, x, y, client):
        self.id = _id
        self.alive = True
        self.position = Position(y, x)
        self.client = client

    def fileno(self):
        return self.client and self.client.fileno() or -1
