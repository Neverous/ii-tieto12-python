# -*- encoding: utf8 -*-
# Maciej Szeptuch 2012

import random
from collections import defaultdict
import pygame
from pygame.locals import *
import utils

class Engine(object):
    """Silnik/Rdzeń gry - łączy menu, gre i edytor w jeden program."""

    def __init__(self, (host, port), debug = False):
        super(Engine, self).__init__()
        self.options = defaultdict(lambda: '', {
            'resolution': 0,
            'resolutions': tuple(reversed(filter(lambda (w, h): w >= 400 and h >= 400, pygame.display.list_modes()))),
            'fullscreen': 0,
            'fps': 60,
            'debug': debug,
            'host': host,
            'port': int(port),
            'client': None,
        })

        self.screen = pygame.display.set_mode(self.getResolution())
        if debug:
            self._debug = pygame.Surface(self.getResolution())
            self._debug.fill((1, 5, 4))
            self._debug.set_colorkey((1, 5, 4))
            self._debug.set_alpha(64)

        self.clock = pygame.time.Clock()
        self._events = ()
        self.active = None
        self._previous = None
        self._modules = defaultdict(lambda: None)

    def addModule(self, module):
        """Instaluje moduł w silniku."""

        self._modules[module.__class__.__name__] = module
        return True

    def removeModule(self, _name):
        """Usuwa moduł z silnika."""

        del self._modules[_name]

    def getModule(self, _name):
        """Zwraca moduł."""

        if not _name in self._modules:
            return None

        return self._modules[_name]

    def activateModule(self, name = None):
        """Ustawia aktywny moduł."""

        if name:
            self._previous = self.active or name
            self.active = name

        return self.active

    def previousModule(self):
        """Aktywuje poprzedni moduł."""

        self.activateModule(self._previous)

    def quit(self):
        """Wyłączanie 'silnika'."""

        raise EngineQuit()

    def events(self):
        """Zwraca wydarzenia dla aktualnej klatki."""

        return self._events

    def tick(self):
        """Przechodzenie do następnej klatki. Ograniczanie maksymalnej liczby FPS."""

        if self.getFPS():
            self.clock.tick(self.getFPS())

        self._events = tuple(pygame.event.get())
        return True

    def _updateScreen(self):
        """Aktualizacja ustawnień ekranu."""

        self.screen = pygame.display.set_mode(self.getResolution(), self.getFullscreen() and pygame.FULLSCREEN)
        if self.options['debug']:
            self._debug = pygame.Surface(self.getResolution())
            self._debug.fill((1, 5, 4))
            self._debug.set_colorkey((1, 5, 4))
            self._debug.set_alpha(64)

        for module in self._modules.values():
            if module: module.screenUpdated()

        return True

    def toggleResolution(self):
        """Zmiana rozdzielczości."""

        self.options['resolution'] += 1
        self.options['resolution'] %= len(self.options['resolutions'])
        return self._updateScreen()

    def getResolution(self):
        """Aktualna rozdzielczość."""

        return self.options['resolutions'][self.options['resolution']]

    def toggleFullscreen(self):
        """Zmiana pełnego ekranu/okna."""

        self.options['fullscreen'] ^= 1
        return self._updateScreen()

    def getFullscreen(self):
        """Pełny ekran/Okno?"""

        return self.options['fullscreen']

    def setFPS(self, fps):
        """Ustawienie maksymalnej liczby FPS."""

        self.options['fps'] = fps
        return True

    def getFPS(self):
        """Maksymalna liczba FPS."""

        return self.options['fps']

    def show(self, surface, updated = None):
        """Rysowanie powierzchni na ekranie. Gdy updated jest None rysuje całą powierzchnię, w przeciwnym przypadku rysuje tylko określone prostokąty."""

        if updated:
            for rect in updated:
                self.screen.blit(surface, rect, rect)
                if self.options['debug']:
                    pygame.draw.rect(self._debug, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), rect)

            if self.options['debug']:
                pygame.draw.rect(self._debug, (255, 255, 255), (0, 0, 50, 20))
                updated.append(utils.drawText(self._debug, "FPS: %d" % (self.clock.get_fps()), 12, (0, 0, 0), (10, 10)))
                self.screen.blit(self._debug, (0, 0))

            pygame.display.update(updated)
            return True

        self.screen.blit(surface, (0, 0))
        if self.options['debug']:
            pygame.draw.rect(self._debug, (255, 255, 255), (0, 0, 50, 20))
            utils.drawText(self._debug, "FPS: %d" % (self.clock.get_fps()), 12, (0, 0, 0), (10, 10))
            self.screen.blit(self._debug, (0, 0))

        pygame.display.update()
        return True

    def run(self):
        """Główna pętla silnika."""

        try:
            while True:
                try:
                    for name, module in self._modules.items():
                        if self.active == name and module:
                            _loaded = 0
                            _surface = module.surface.copy()
                            while _loaded < 255 and self.tick():
                                _loaded += 15
                                _surface.set_alpha(_loaded)
                                self.show(_surface)

                            module.show()
                            break

                except ModuleQuit:
                    pass

        except EngineQuit:
            pass

class EngineQuit(Exception):
    """Wyjście z silnika."""

    pass

class Module(object):
    """Podstawowy moduł dla silnika."""

    def __init__(self, _engine):
        super(Module, self).__init__()
        self._engine = _engine
        self._resx, self._resy = _engine.getResolution()

    def screenUpdated(self):
        """Aktualizacja ustawień ekranu."""

        self._resx, self._resy = self._engine.getResolution()

    def show(self):
        """Pokazuje moduł."""

        pass

class ModuleQuit(Exception):
    """Uniwersalne wyjście z modułu."""

    pass
