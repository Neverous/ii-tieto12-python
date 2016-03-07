# -*- encoding: utf-8 -*-
# Serwer do obsługi gry

import sys
import random
import socket
import select
import logging
import time
from collections import deque
import cPickle as pickle
from protocolObjects import *
from cStringIO import StringIO

MAX_LISTEN_QUEUE = 128
BUFFER_SIZE = 4096
MINE = 2**64

class Server(object):
    '''Serwer obługujący grę do zadania 2.'''

    def __init__(self, host, port = 6666, players = 2, mapSize = (20, 20)):
        self._host = host
        self._port = port
        self._socket = None

        self._playersCount = min(players, 64)
        self._mapSize = mapSize
        self._players = None
        self._mines = None
        self._map = None
        self._asked = None

        # Debug
        self._debug = logging.getLogger('GameServer')

    def _read(self, _sock):
        if not _sock: return None
        _rd, _, _ = select.select([_sock], [], [], 0.2)
        if not _rd: return None
        try:
            return _sock.recv(4096)

        except socket.error, err:
            self._debug.error('Socket error: %s', err)
            return ''

    def _write(self, _sock, data):
        if not _sock: return 0
        _, _wr, _ = select.select([], [_sock], [], 0.2)
        if not _wr: return 0
        try:
            return _sock.send(data)

        except socket.error, err:
            self._debug.error('Socket error: %s', err)
            return 0

    def _startListener(self):
        self._players = []
        # Ustawianie gniazda nasłuchującego
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket.setblocking(False)
        self._socket.bind((self._host, self._port))
        self._socket.listen(MAX_LISTEN_QUEUE)
        self._debug.info('Serwer gry działa na %s:%d', self._host, self._port)

    def _stopListener(self):
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()

        except socket.error:
            pass

        self._socket = None
        self._debug.info('Serwer zakończył przyjmowanie nowych klientów!')

    def run(self):
        while True:
            self._debug.info('Rozpoczynanie nowej gry.')
            self.pregame()
            self.ingame()
            self.postgame()
            time.sleep(5)

    def pregame(self):
        _clients = []
        self._startListener()
        while len(_clients) != self._playersCount:
            _rd, _, _er = select.select([self._socket] + _clients, [], [self._socket] + _clients, 10)
            if not _rd and not _er:
                self._debug.debug('Oczekiwanie na połączenia...')
                continue

            for _sock in _rd:
                if _sock == self._socket:
                    _client, _addr = self._socket.accept()
                    self._debug.info('Klient %s:%d przyłączył się!', *_addr)
                    _clients.append(_client)

                elif self._read(_sock) == '':
                    _er.append(_sock)

            for error in _er:
                if error == self._socket:
                    raise RuntimeError('Błąd gniazda nasłuchującego')

                self._debug.info('Klient %s:%d rozłączył się!', *_sock.getpeername())
                _clients.remove(error)

        self._stopListener()
        self._debug.info('Pomyślnie połączono %d klientów!', len(_clients))
        self._mines = []
        for _id, _client in enumerate(_clients):
            self._debug.info('Gracz %d - %s:%d.', _id, *_client.getpeername())
            self._players.append(Player(_id, random.randint(1, self._mapSize[0]), random.randint(1, self._mapSize[1]), _client))

        # ODLICZANIE
        for c in xrange(3, 0, -1):
            self._debug.info("Odliczanie: %d...", c)
            for _player in self._players:
                self._write(_player.client, pickle.dumps(Countdown(c, Position(self._mapSize[1], self._mapSize[0]), _player.id)))

            time.sleep(1)

        _players = [_player.position for _player in self._players if _player.alive]
        for _player in self._players:
            self._write(_player.client, pickle.dumps(Map(self._mines, _players)))

        self._map = [[0 for _ in xrange(self._mapSize[0])] for _ in xrange(self._mapSize[1])]
        for _player in self._players:
            self._map[_player.position.y - 1][_player.position.x - 1] |= 2**_player.id

    def ingame(self):
        _output = ['' for _ in xrange(self._playersCount)]
        _input = ['' for _ in xrange(self._playersCount)]
        _cnt = 0
        _playing = True
        self._asked = None
        while _playing and len([_player for _player in self._players if _player.alive]) > 1:
            _playing = filter(lambda x: x.fileno() != None, self._players)
            _rd, _wr, _er = select.select(_playing, filter(lambda x: _output[x.id], _playing), _playing, 10)
            if not _rd and not _wr and not _er:
                _cnt += 1
                self._debug.debug('Nikt nie gra' + '.'*_cnt)
                if _cnt > 6:
                    self._debug.info('Nikt nie gra. Zamykanie rozgrywki!')
                    break

                continue

            _cnt = 0
            for write in _wr:
                count = self._write(write.client, _output[write.id])
                _output[write.id] = _output[write.id][count:]

            for read in _rd:
                _tmp = self._read(read.client)
                if _tmp == '':
                    _er.append(read)
                    continue

                _input[read.id] += _tmp
                obj = None
                try:
                    ss = StringIO(_input[read.id])
                    obj = pickle.load(ss)
                    _input[read.id] = ss.read()

                except (EOFError, pickle.UnpicklingError, ValueError, AttributeError), err:
                    if not isinstance(err, EOFError):
                        self._debug.debug('%s: %s', err.__class__.__name__, err)

                    obj = None

                if isinstance(obj, PlayerAction):
                    _player = self._players[read.id]
                    x, y = _player.position.x - 1, _player.position.y - 1
                    self._debug.debug('Gracz %d próbuje wykonać ruch: %s', read.id, obj.action)
                    if obj.action == 'm': # Odśwież mapę
                        self._debug.debug('Gracz %d odświeża mapę', read.id)
                        _output[read.id] += pickle.dumps(Map(self._mines, [_player.position for _player in self._players if _player.alive]))
                        continue

                    elif obj.action == 'e':
                        self._debug.debug('Gracz %d kończy grę', read.id)
                        self._asked = read.id
                        return

                    if not _player.alive:
                        self._debug.debug('Gracz nie żyje, nie może się ruszać')
                        _output[read.id] += pickle.dumps(Map(self._mines, [_player.position for _player in self._players if _player.alive]))
                        continue

                    if obj.action == 'c': # Stawia minę
                        self._debug.debug('Gracz %d stawia minę na polu [%d,%d]', read.id, _player.position.x, _player.position.y)
                        if self._map[y][x] & MINE == 0:
                            self._map[y][x] |= MINE
                            self._mines.append(Mine(Position(_player.position.y, _player.position.x), _player.id))

                    elif obj.action in ('u', 'd', 'l', 'r'): # rusza się
                        self._debug.debug('Gracz %d próbuje się ruszyć.', read.id)
                        dx, dy = {
                            'u': (0, -1),
                            'd': (0, 1),
                            'l': (-1, 0),
                            'r': (1, 0),
                        }[obj.action]

                        if 0 <= x + dx < self._mapSize[0] and 0 <= y + dy < self._mapSize[1]:
                            self._map[y][x] ^= 2**_player.id
                            self._map[y + dy][x + dx] ^= 2**_player.id
                            _player.position.x += dx
                            _player.position.y += dy
                            if self._map[y + dy][x + dx] & MINE:
                                _player.alive = False

                    else:
                        self._debug.debug('Nieznany ruch "%s" gracza %d', obj.action, read.id)

                    _output[read.id] += pickle.dumps(Map(self._mines, [_player.position for _player in self._players if _player.alive]))

                elif obj:
                    self._debug.error('Nieprawidłowy obiekt! %s', obj.__class__.__name__)
                    _er.append(read)

            for error in _er:
                self._debug.error('Gracz %d rozłączył się!', error.id)
                del error.client
                error.alive = False
                error.client = None

    def postgame(self):
        self._debug.debug('Przeliczanie wyników')
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
        for _player in self._players:
            self._write(_player.client, pickle.dumps(Result(winners, scores)))

        self._debug.info('Rozłączanie graczy!')
        for _player in self._players:
            if not _player.client: continue
            try:
                _player.client.shutdown(socket.SHUT_RDWR)
                _player.client.close()

            except socket.error:
                pass

            del _player.client

        self._players = None
        self._mines = None
        self._map = None

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG)
    if len(sys.argv) < 6:
        print 'usage: %s host port players mapWidth mapHeight' % (sys.argv[0])
        sys.exit(1)

    srv = Server(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), (int(sys.argv[4]), int(sys.argv[5])))
    try:
        srv.run()

    except KeyboardInterrupt:
        print 'cya!'
        sys.exit(0)
