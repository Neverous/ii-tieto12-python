# -*- encoding: utf-8 -*-
# Serwer do obsługi gry

import sys
import random
import socket
import select
import logging
import time
import cPickle as pickle
from cStringIO import StringIO
from protocolObjects import *
import time

BUFFER_SIZE = 4096

class Client(object):
    '''Klient do gry.'''

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._socket = None
        self.map = None
        self.countdown = None
        self.result = None
        self._output = ''
        self._input = ''
        self._sleep = 0
        self._cnt = 0
        self._last = 0

        # Debug
        self._debug = logging.getLogger('GameClient')

    def _read(self, _sock):
        if not _sock: return None
        _rd, _, _ = select.select([_sock], [], [], 0.001)
        if not _rd: return None
        return _sock.recv(4096)

    def _write(self, _sock, data):
        if not _sock: return 0
        _, _wr, _ = select.select([], [_sock], [], 0.001)
        if not _wr: return 0
        try:
            return _sock.send(data)

        except socket.error:
            return 0

    def _startClient(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket.connect((self._host, self._port))
        self._socket.setblocking(False)
        self._debug.info('Klient podłączył się do %s:%d', self._host, self._port)

    def _stopClient(self):
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()

        except socket.error:
            pass

        self._socket = None
        self._debug.info('Klient rozłączył się od serwera!')

    def update(self, timeout):
        if not self._socket:
            try:
                self._startClient()

            except socket.error, err:
                self._debug.debug('%s', err)
                return 'Blad polaczenia: %s' % err

        _rd, _wr, _er = select.select([self._socket], self._output and [self._socket] or [], [self._socket], timeout)
        if not _rd and not _er and not _wr:
            _act = time.time()
            if _act - self._sleep > 10:
                self._cnt += 1
                self._debug.debug('Nic się nie dzieje' + '.'*self._cnt)
                self._sleep = _act
                if self._cnt > 18:
                    self._debug.error('Zbyt długi czas oczekiwania na ruch')
                    return 'Zbyt dlugi czas oczekiwania!'

            return True

        self._cnt = 0
        for write in _wr:
            count = self._write(write, self._output)
            self._output = self._output[count:]

        for read in _rd:
            _tmp = self._read(self._socket)
            if _tmp == '':
                _er.append(read)
                continue

            self._input += _tmp
            obj = None
            while True:
                try:
                    ss = StringIO(self._input)
                    obj = pickle.load(ss)
                    self._input = ss.read()

                except (EOFError, pickle.UnpicklingError, ValueError, AttributeError), err:
                    if not isinstance(err, EOFError):
                        self._debug.debug('%s: %s', err.__class__.__name__, err)

                    obj = None
                    break

                if isinstance(obj, Countdown):
                    self._debug.debug('Licznik: %d', obj.number)
                    self.countdown = obj

                elif isinstance(obj, Map):
                    self._debug.debug('Stan gry!')
                    self.map = obj
                    self.countdown = None

                elif isinstance(obj, Result):
                    self._debug.debug('Wyniki!')
                    self.result = obj

                elif obj:
                    self._debug.error('Nieprawidłowy obiekt! %s', obj.__class.__name__)
                    _er.append(read)

                else:
                    break

        for error in _er:
            self._debug.error('Błąd połączenia!')
            self._stopClient()
            return 'Blad polaczenia!'

        return True

    def sendAction(self, action):
        self._output += pickle.dumps(PlayerAction(action))
        return True
