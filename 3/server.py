# -*- encoding: utf-8 -*-
# Serwer do obsługi gry z wykorzystaniem Twisted

import sys
import random
import logging
import time
from twisted.internet.protocol import Protocol, Factory
from collections import deque
import cPickle as pickle
from protocolObjects import *
from cStringIO import StringIO

MAX_LISTEN_QUEUE = 128
MINE = 2**64

STATE_WAITING_FOR_PLAYERS   = 0
STATE_STARTING_GAME         = 1
STATE_PLAYING_GAME          = 2

class BomberProtocol(Protocol):
    def __init__(self):
        self._debug = logging.getLogger('BomberProtocol')

    def connectionMade(self):
        self.input = ''
        self.player = None
        if not self.factory.appendClient(self):
            self.transport.loseConnection()
            return

        self._debug.info('Nowy klient dołączył do gry!')

    def connectionLost(self, reason):
        self._debug.info('Klient rozłączył się: %s.', reason)
        self.input = ''
        self.factory.removeClient(self)
        self.player = None
        self.factory = None

    def dataReceived(self, data):
        if self.factory.state != STATE_PLAYING_GAME or not self.player:
            return

        self.input += data
        try:
            ss = StringIO(self.input)
            obj = pickle.load(ss)
            self.input = ss.read()

        except (EOFError, pickle.UnpicklingError, ValueError, AttributeError), err:
            if not isinstance(err, EOFError):
                self._debug.error('%s: %s', err.__class__.__name__, err)

            obj = None

        if not obj:
            return

        if isinstance(obj, PlayerAction):
            self._debug.debug('Gracz %d próbuje wykonać ruch: %s', self.player.id, obj.action)
            if not self.player.alive:
                self._debug.debug('Gracz %d nie żyje, nie może się ruszać', self.player.id)

            elif obj.action == 'm': # Odśwież mapę
                self._debug.info('Gracz %d odświeża mapę', self.player.id)

            elif obj.action == 'e':
                self._debug.info('Gracz %d kończy grę', self.player.id)
                self.factory.checkAlive(self.player.id)

            elif obj.action == 'c': # Stawia minę
                self._debug.info('Gracz %d stawia minę na polu [%d,%d]', self.player.id, self.player.position.x, self.player.position.y)
                self.player.putMine()

            elif obj.action in ('u', 'd', 'l', 'r'): # rusza się
                self._debug.info('Gracz %d próbuje się ruszyć.', self.player.id)
                dx, dy = {
                    'u': (0, -1),
                    'd': (0, 1),
                    'l': (-1, 0),
                    'r': (1, 0),
                }[obj.action]

                self.player.move((dx, dy))
                self.factory.checkAlive()

            else:
                self._debug.warning('Nieznany ruch "%s" gracza %d', obj.action, self.player.id)

            self.transport.write(pickle.dumps(self.factory.getMap()))
            return

        self._debug.error('Gracz %d: Nieprawidłowy obiekt! %s', self.player.id, obj.__class__.__name__)
        self.transport.loseConnection()

class BomberFactory(Factory):
    protocol = BomberProtocol
    def __init__(self, players = 2, mapSize = (20, 20)):
        self._playersCount = min(players, 64)
        self._mapSize = mapSize
        self._debug = logging.getLogger('BomberFactory')
        self._newGame()

    def _newGame(self):
        self._debug.info('Rozpoczynanie nowej gry!')
        self._players = []
        self._clients = []
        self._mines = []
        self._map = [[0 for _ in xrange(self._mapSize[0])] for _ in xrange(self._mapSize[1])]
        self._asked = None
        self._countdown = 3
        self.state = STATE_WAITING_FOR_PLAYERS

    def appendClient(self, client):
        if self.state != STATE_WAITING_FOR_PLAYERS:
            return False

        self._clients.append(client)
        if len(self._clients) == self._playersCount:
            from twisted.internet import reactor
            reactor.callLater(0, self.pregame, True)

        return True

    def removeClient(self, client):
        if client.player:
            client.player.alive = False

        if client in self._clients:
            self._clients.remove(client)
            self.checkAlive()

        return True

    def checkAlive(self, _ask = None):
        if self.state == STATE_WAITING_FOR_PLAYERS:
            return

        if not self._asked and _ask:
            self._asked = _ask

        if _ask or len([_player for _player in self._players if _player.alive]) <= 1:
            from twisted.internet import reactor
            reactor.callLater(0, self.postgame)

    def getMap(self):
        return Map(self._mines, [_player.position for _player in self._players if _player.alive])

    def getMine(self, (x, y)):
        return self._map[y][x] & MINE

    def putMine(self, _id, _pos):
        if self._map[_pos.y - 1][_pos.x - 1] & MINE == 0:
            self._map[_pos.y - 1][_pos.x - 1] |= MINE
            self._mines.append(Mine(Position(_pos.y, _pos.x), _id))

        return True

    def movePlayer(self, _id, (sx, sy), (ex, ey)):
        if 0 <= ex < self._mapSize[0] and 0 <= ey < self._mapSize[1]:
            self._map[sy][sx] ^= 2**_id
            self._map[ey][ex] ^= 2**_id
            return True

        return False

    def pregame(self, start = False):
        if self.state == STATE_WAITING_FOR_PLAYERS and start:
            self.state = STATE_STARTING_GAME
            # PLAYERS
            for _id, _client in enumerate(self._clients):
                _client.player = Player(_id, (random.randint(1, self._mapSize[0]), random.randint(1, self._mapSize[1])), _client)
                self._players.append(_client.player)

            for _player in self._players:
                if _player.alive:
                    self._map[_player.position.y - 1][_player.position.x - 1] |= 2**_player.id

        elif self.state != STATE_STARTING_GAME:
            return

        self._debug.info('State: %d', self.state)
        # COUNTDOWN
        if self._countdown:
            self._debug.info('Odliczanie: %d...', self._countdown)
            for _player in self._players:
                _player.client.transport.write(pickle.dumps(Countdown(self._countdown, Position(self._mapSize[1], self._mapSize[0]), _player.id)))

            self._countdown -= 1
            from twisted.internet import reactor
            reactor.callLater(1, self.pregame)
            return

        _players = [_player.position for _player in self._players if _player.alive]
        for _player in self._players:
            _player.client.transport.write(pickle.dumps(Map(self._mines, _players)))

        self.state = STATE_PLAYING_GAME

    def postgame(self):
        if self.state == STATE_WAITING_FOR_PLAYERS:
            return

        self._debug.info('Przeliczanie wyników')
        _counts = [0]
        _counter = 0
        _wrap = [0 for _ in xrange(self._playersCount)]
        def BFS((x, y), _id):
            que = deque([(x, y)])
            for p in xrange(self._playersCount):
                if self._map[y][x] & 2**p:
                    _wrap[p] = _id

            self._map[y][x] = MINE
            while que:
                x, y = que.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < self._mapSize[0] and 0 <= y + dy < self._mapSize[1] and\
                       self._map[y + dy][x + dx] & MINE == 0:
                        _counts[_id] += 1
                        if self._map[y + dy][x + dx] != 0:
                            for p in xrange(self._playersCount):
                                if self._map[y + dy][x + dx] & 2**p:
                                    _wrap[p] = _id

                        self._map[y + dy][x + dx] = MINE
                        que.append((x + dx, y + dy))

        for h in xrange(self._mapSize[1]):
            for w in xrange(self._mapSize[0]):
                if self._map[h][w] & MINE: continue
                _counter += 1
                _counts.append(1)
                BFS((w, h), _counter)

        scores = [_counts[_wrap[_id]] for _id in xrange(self._playersCount)]
        _max = max(scores)
        winners = _max and list(filter(lambda x: scores[x] == _max, xrange(self._playersCount))) or []
        if len(winners) > 1 and self._asked in winners:
            winners.remove(self._asked)

        self._debug.info('Wysyłanie wyników! %s %s', winners, scores)
        for _client in self._clients:
            _client.transport.write(pickle.dumps(Result(winners, scores)))

        self._debug.info('Rozłączanie graczy!')
        for _client in self._clients:
            _client.transport.loseConnection()
            del _client

        from twisted.internet import reactor
        reactor.callLater(0, self._newGame)

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG)
    if len(sys.argv) < 6:
        print 'usage: %s host port players mapWidth mapHeight' % (sys.argv[0])
        sys.exit(1)

    factory = BomberFactory(int(sys.argv[3]), (int(sys.argv[4]), int(sys.argv[5])))
    try:
        from twisted.internet import reactor
        reactor.listenTCP(int(sys.argv[2]), factory, MAX_LISTEN_QUEUE, sys.argv[1])
        reactor.run()

    except KeyboardInterrupt:
        pass

    print 'cya!'
    sys.exit(0)
