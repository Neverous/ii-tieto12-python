# -*- encoding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory

class ControlProtocol(Protocol):
    def connectionMade(self):
        self.input = ''

    def connectionLost(self, reason):
        self.input = ''

    def dataReceived(self, data):
        self.input += data
        while '\r\n' in self.input:
            cmd, self.input = self.input.split('\r\n', 1)
            if cmd == 'STATS':
                self.transport.write('\n'.join(['%s=%s' % (key, str(value)) for key, value in self.factory.server.stats.items()]) + '\r\n')

            elif cmd == 'QUIT':
                self.transport.loseConnection()
                return

            else:
                self.transport.write('ERR Invalid command!\r\n')

class ControlFactory(Factory):
    protocol = ControlProtocol
    def __init__(self, _server):
        self.server = _server
