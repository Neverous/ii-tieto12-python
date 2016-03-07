import sys, socket, curses, select, cPickle
import time
from protocolObjects import *

class Client( object ):
    def __init__(self, address, port):
        self.makeConnection( address, port )
        self.boardDrawn = False
        self.playerId = None

    def makeConnection(self, address, port):
        port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))
        self.socket.setblocking(0)
        print "Connected to %s:%d" % (address, port)

    def send(self, obj):
        _, toWrite, _ = select.select([], [self.socket], [])
        res = toWrite[0].sendall( cPickle.dumps( obj ) )
        if res: raise Exception("Problem during sending a message to socket: %s" % res)

    def receive(self):
        toRead, _, _ = select.select([self.socket], [], [])
        rec = toRead[0].recv(4096)
        if len(rec) == 0:
            return None
        data = None
        while data == None:
            try:
                data = cPickle.loads( rec )
            except (EOFError, cPickle.UnpicklingError, ValueError):
                rec += toRead[0].recv(4096)
        return data

    def configureCurses(self):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def drawBoard(self, mapSize):
        self.mapWindow = self.stdscr.subwin( mapSize.y + 2, mapSize.x + 2, 0, 0)
        self.mapWindow.border()
        self.mapWindow.refresh()
        self.boardDrawn = True

    def updateBoard(self, mines):
        self.mapWindow.clear()
        self.mapWindow.border()
        for mine in mines:
            self.mapWindow.addstr( mine.position.y, mine.position.x, '.', curses.color_pair(mine.playerId + 1) )

    def drawCountdown(self, number):
        y, x = self.mapWindow.getmaxyx()
        self.mapWindow.addstr( y/2 - 1, x/2 - 8, 'You are player %d' % (self.playerId + 1), curses.color_pair(self.playerId + 1) )
        self.mapWindow.addstr( y/2, x/2, str(number), curses.color_pair(5) )

    def drawPlayer(self, playerId, position):
        if position.y > 0 and position.x > 0:
            self.mapWindow.addstr( position.y, position.x, 'P', curses.color_pair(playerId + 1) )

    def drawResult(self, result):
        y, x = self.mapWindow.getmaxyx()
        if len( result.winners ) > 1:
            str = 'The winners are Players'
            for id in result.winners:
                str += ' %d,' % (id + 1)
            str = str[:-1] + '!'
            self.mapWindow.addstr( y/2, x/2 - 10, str, curses.color_pair(5) )
        else:
            self.mapWindow.addstr( y/2, x/2 - 10, 'The winner is Player %d!' % (result.winners[0] + 1), curses.color_pair(5) )
        if len( result.scores ) > 0:
            resStr = 'The scores are:\t'
            for id, score in enumerate( result.scores ):
                resStr += 'Player %d: %d, ' % (id + 1, score)
            self.mapWindow.addstr( y/2 + 1, 10, resStr[:-2], curses.color_pair(5) )
        else:
            self.mapWindow.addstr( y/2 + 1, x/2 - 10, 'Player %d was the last man alive!' % (result.winners[0] + 1), curses.color_pair(5) )

    def makeAction(self, action):
        self.send( PlayerAction( action ) )

    def play(self, stdscr):
        self.configureCurses()
        self.stdscr = stdscr
        while True:
            data = self.receive()
            if data == None: continue
            if isinstance(data, Countdown):
                if not self.boardDrawn:
                    self.drawBoard( data.mapSize )
                    self.playerId = int( data.playerId )
                self.drawCountdown( data.number )
                self.mapWindow.refresh()
            elif isinstance(data, Map):
                self.updateBoard( data.mines )
                for i, pos in enumerate( data.playersPositions ):
                    self.drawPlayer( i, pos )
                self.mapWindow.refresh()
                key = self.stdscr.getch()
                if key == ord(' '): self.makeAction('m')
                elif key == curses.KEY_UP: self.makeAction('u')
                elif key == curses.KEY_DOWN: self.makeAction('d')
                elif key == curses.KEY_LEFT: self.makeAction('l')
                elif key == curses.KEY_RIGHT: self.makeAction('r')
                elif key == curses.KEY_END: self.makeAction('e')
                elif key == curses.KEY_DC: self.makeAction('c')
                else: self.makeAction('m')
            elif isinstance(data, Result):
                self.drawResult( data )
                self.mapWindow.refresh()
                raw_input()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError("Incorrect number of arguments. You should pass ip:port as only argument.")
    host, port = sys.argv[1].split(':')
    client = Client( host, port )
    curses.wrapper( client.play )
