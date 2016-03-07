# -*- encoding: utf-8 -*-

import logging
import time
from twisted.internet.protocol import Protocol, Factory
from protocolObjects import *
try:
    import cPickle as pickle

except ImportError:
    print 'WARNING: cPickle not available!'
    import pickle

try:
    from cStringIO import StringIO

except ImportError:
    print 'WARNING: cStringIO not available!'
    from StringIO import StringIO

class GameClient(Protocol):
    def __init__(self):
        self._debug = logging.getLogger('GameClient')
        self.input = None

    def connectionMade(self):
        self.input = ''
        self.factory.client = self
        self._debug.info('Podłączono do serwera!')

    def connectionLost(self, reason):
        self._debug.info('Utracono połączenie: %s.', reason)
        self.factory.error(reason)
        self.input = ''
        self.factory.client = None

    def dataReceived(self, data):
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

        if isinstance(obj, Countdown):
            self._debug.debug('Licznik: %d', obj.number)

        elif isinstance(obj, Map):
            self._debug.debug('Stan gry!')

        elif isinstance(obj, Result):
            self._debug.debug('Wyniki!')

        elif obj:
            self._debug.error('Nieprawidłowy obiekt! %s', obj.__class__.__name__)
            self.factory.error('Nieprawidłowy obiekt: %s' % obj)
            return

        self.factory.process(obj)

    def sendAction(self, action):
        self.transport.write(pickle.dumps(PlayerAction(action)))
        return True

class BomberFactory(Factory):
    protocol = GameClient

    def __init__(self, callback, errback):
        self.client = None
        self.process = callback
        self.error = errback
        self._debug = logging.getLogger('BomberFactory')

    def sendAction(self, action):
        if not self.client:
            return False

        return self.client.sendAction(action)

    def startedConnecting(self, connector):
        self._debug.info('Rozpoczynanie połączenia.')

    def clientConnectionLost(self, connector, reason):
        self._debug.warning('Utracono połączenie!')

    def clientConnectionFailed(self, connector, reason):
        self._debug.warning('Połączenie nie powiodło się!')
        from twisted.internet import reactor
        reactor.callLater(5, lambda: connector.connect())
