# -*- encoding: utf8 -*-
# Maciej Szeptuch 2012

import time
import pygame
import engine
import utils
import time
from pygame.locals import *
from menu import MenuButton, MenuQuit
from map import Map, ObjectsLayer
import protocolObjects
import sock

class Scene(engine.Module):
    """Główny ekran gry."""

    def __init__(self, _engine):
        super(Scene, self).__init__(_engine)
        self._background = pygame.Surface((self._resx, self._resy))
        self.surface = self._background.copy()
        self._actual = []
        self._client = _engine.options['client'] = sock.BomberFactory(self._process, self._connectionError)
        from twisted.internet import reactor
        from twisted.internet.task import LoopingCall
        self._gameloop = LoopingCall(self._render)
        self._network = reactor.connectTCP(_engine.options['host'], _engine.options['port'], self._client)
        self._play = True
        self._refresh = True
        self._submodules = ()
        self._map = None
        self._playerID = None

    def __del__(self):
        self._network.disconnect()

    def _loadMap(self, _width, _height):
        self._map = Map(self._engine, self, (_width, _height))
        self._heroLayer = ObjectsLayer(self._map) # Warstwa graczy
        self._mineLayer = ObjectsLayer(self._map) # Warstwa min
        self._map.addLayer('Hero', 3, self._heroLayer)
        self._map.addLayer('Mine', 2, self._mineLayer)
        self._submodules = (self._map,)

    def isPlaying(self):
        """Czy gracz nadal gra?"""

        return self._play

    def screenUpdated(self):
        """Aktualizuje obrazy tła i submoduły."""

        super(Scene, self).screenUpdated()
        self._refresh = True
        self._background = pygame.Surface((self._resx, self._resy))
        self.surface = pygame.transform.smoothscale(self.surface, (self._resx, self._resy))
        for submodule in self._submodules:
            submodule.screenUpdated()

    def show(self):
        if not self._play:
            self._engine.previousModule()
            return

        self._last = time.time()
        from twisted.internet import reactor
        self._gameloop.start(self._engine.getFPS() and 1.0 / self._engine.getFPS() or 0.0)
        reactor.run()
        self._gameloop.stop()

    def _render(self):
        self._engine.tick()
        for event in self._engine.events():
            if event.type == QUIT:
                self._play = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self._engine.runLoop = False
                    from twisted.internet import reactor
                    reactor.stop()
                    return

                if self._map:
                    if event.key in (K_w, K_UP):
                        self._client.sendAction('u')
                        self._last = time.time()

                    elif event.key in (K_s, K_DOWN):
                        self._client.sendAction('d')
                        self._last = time.time()

                    elif event.key in (K_a, K_LEFT):
                        self._client.sendAction('l')
                        self._last = time.time()

                    elif event.key in (K_d, K_RIGHT):
                        self._client.sendAction('r')
                        self._last = time.time()

                    elif event.key in (K_RETURN, K_RCTRL, K_LCTRL):
                        self._client.sendAction('c')
                        self._last = time.time()

                    elif event.key == K_q:
                        self._client.sendAction('e')
                        self._last = time.time()

        if self._map and self._last + 1./self._engine.options['fps'] < time.time():
            self._client.sendAction('m')
            self._last = time.time()

        if not self._map and self._playerID == None:
            self.surface = self._background.copy()
            utils.drawText(self.surface, 'Oczekiwanie na graczy!', 20, (255, 255, 255), (self._resx / 2, self._resy / 2))

        updated = []
        if self._play:
            for submodule in self._submodules:
                updated.extend(submodule.update())
                submodule.draw(self.surface)

        if self._refresh:
            self._engine.show(self.surface)
            self._refresh = False

        else:
            self._engine.show(self.surface, updated)

        if not self._play:
            time.sleep(5)
            self._engine.runLoop = False
            from twisted.internet import reactor
            reactor.stop()
            return

    def _process(self, obj):
        if isinstance(obj, protocolObjects.Countdown):
            return self._countdown(obj)

        if isinstance(obj, protocolObjects.Result):
            return self._finish(obj)

        if isinstance(obj, protocolObjects.Map):
            return self._update(obj)

        return self._connectionError(obj)

    def _connectionError(self, msg):
        self._play = False
        utils.drawText(self.surface, str(msg), 10, (255, 255, 255), (self._resx / 2, self._resy - 10))

    def _countdown(self, countdown):
        if not self._map and countdown.number == 1:
            self._loadMap(countdown.mapSize.x, countdown.mapSize.y)

        if self._playerID == None:
            self._playerID = countdown.playerId

        self.surface = self._background.copy()
        utils.drawText(self.surface, 'Gracz %d. >%d<' % (countdown.playerId, countdown.number), 30, (255, 255, 255), (self._resx / 2, self._resy / 2))

    def _finish(self, result):
        self.surface = self._background.copy()
        utils.drawText(self.surface, 'Gra zakonczona!', 40, (255, 255, 255), (self._resx / 2, self._resy / 2))
        if len(result.winners) == 1:
            utils.drawText(self.surface, 'Wygral gracz %d!' % result.winners[0], 40, (255, 255, 255), (self._resx / 2, self._resy / 2 + 40))

        elif len(result.winners):
            utils.drawText(self.surface, 'Wygrali gracze %s!' % (', '.join([str(i) for i in result.winners])), 40, (255, 255, 255), (self._resx / 2, self._resy / 2 + 40))

        self._play = False
        self._engine.show(self.surface)

    def _update(self, map):
        if not self._map:
            self._play = False
            return

        for mine in map.mines:
            _id = mine.position.x, mine.position.y
            if not self._mineLayer.get(_id):
                _mine = ObjectsLayer.Sprite(utils.loadImage('gfx/bomb.png', alpha = True))
                self._mineLayer.add(_id, _mine)
                self._mineLayer.move(_id, _id)

        for _id, player in enumerate(map.playersPositions):
            if not self._heroLayer.get(_id):
                self._heroLayer.add(_id, ObjectsLayer.Sprite(utils.loadImage('gfx/hero/n.png', alpha = True)))

            _hero = self._heroLayer.get(_id)
            _pos = _hero.getPos()
            self._heroLayer.move(_id, (player.x, player.y))
            _newpos = _hero.getPos()
            if _pos[0] > _newpos[0]:
                _hero.changeImage(utils.loadImage('gfx/hero/w.png', alpha = True))

            if _pos[0] < _newpos[0]:
                _hero.changeImage(utils.loadImage('gfx/hero/e.png', alpha = True))

            if _pos[1] > _newpos[1]:
                _hero.changeImage(utils.loadImage('gfx/hero/n.png', alpha = True))

            if _pos[1] < _newpos[1]:
                _hero.changeImage(utils.loadImage('gfx/hero/s.png', alpha = True))

            if _id == self._playerID:
                _, _, w, h = self._map.getRectangle()
                self._map.setShift((w / 2 - _newpos[0], h / 2 - _newpos[1]))

class NewGameButton(MenuButton):
    """Przycisk nowej gry."""

    def __init__(self, _engine):
        super(NewGameButton, self).__init__(_engine, 'Nowa gra')

    def update(self):
        """Zmiana napisu z kontynuuj na Nowa gra."""

        _scene = self._engine.getModule('Scene')
        if not _scene:
            return

        if self.text == 'Nowa gra' and _scene.isPlaying():
            self.text = 'Kontynuuj'

        elif self.text == 'Kontynuuj' and not _scene.isPlaying():
            self.text = 'Nowa gra'

    def callback(self):
        """Rozpoczynanie nowej gry."""

        _scene = self._engine.getModule('Scene')
        if not _scene or not _scene.isPlaying():
            self._engine.addModule(Scene(self._engine))

        self._engine.activateModule('Scene')
        raise MenuQuit()

