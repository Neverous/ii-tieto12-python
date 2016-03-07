# -*- encoding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory

class ControlProtocol(Protocol):
    def connectionMade(self):
        self.input = ''
        self.transport.write('STATS\r\n')

    def connectionLost(self, reason):
        self.input = ''

    def dataReceived(self, data):
        self.input += data
        if self.input.endswith('\r\n'):
            self.factory.reply.callback(self.input[:-2])
            self.transport.loseConnection()
            return

class ControlFactory(Factory):
    protocol = ControlProtocol
    def __init__(self, _reply):
        self.reply = _reply

    def startedConnecting(self, connector):
        pass

    def clientConnectionLost(self, connector, reason):
        from twisted.internet import reactor
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        from twisted.internet import reactor
        reactor.stop()
