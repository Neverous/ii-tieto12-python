# -*- encoding: utf8 -*-
# Maciej Szeptuch 2012

import pygame
from pygame.locals import *
import engine
import utils

class Menu(engine.Module):
    """Menu główne."""

    def __init__(self, _engine, _buttons):
        super(Menu, self).__init__(_engine)
        self.image = utils.loadImage('data/gfx/menu.jpg')
        self.logo = utils.loadImage('data/gfx/logo.png', alpha = True)
        self._resx, self._resy = self._engine.getResolution()
        self._background = pygame.transform.smoothscale(self.image, (self._resx, self._resy))
        self._background.blit(self.logo, (self._resx / 2 - self.logo.get_size()[0] / 2, 100)) # rysuje wyśrodkowane logo
        self.surface = self._background.copy()
        self._focus = 0
        self._buttons = _buttons
        self._updated = []

    def screenUpdated(self):
        """Aktualizacja tła."""

        self._resx, self._resy = self._engine.getResolution()
        self._background = pygame.transform.smoothscale(self.image, (self._resx, self._resy))
        self._background.blit(self.logo, (self._resx / 2 - self.logo.get_size()[0] / 2, 100))
        self.surface = pygame.transform.scale(self.surface, (self._resx, self._resy))
        self._updated = [(0, 0, self._resx, self._resy)]

    def show(self):
        """Wyświetlanie menu."""

        try:
            while self._engine.tick():
                for button in self._buttons:
                    button.update()

                for event in self._engine.events():
                    if event.type == QUIT:
                        raise engine.EngineQuit()

                    if event.type == KEYUP:
                        if event.key == K_ESCAPE:
                            self._engine.previousModule()
                            raise MenuQuit()

                        if event.key in (K_UP, K_DOWN):
                            _step = event.key == K_UP and -1 or 1
                            self._focus = (self._focus + _step) % len(self._buttons)
                            while not self._buttons[self._focus].active:
                                self._focus = (self._focus + _step) % len(self._buttons)

                        elif event.key == K_RETURN:
                            self._buttons[self._focus].callback()

                self.surface = self._background.copy()
                _shift = 300
                for n, button in enumerate(self._buttons):
                    button.update()
                    x, y, width, height = utils.drawText(self.surface, button.text, 14, (self._focus == n and (255, 0, 0)) or (button.active and (255, 255, 255)) or (128, 128, 128), (self._resx/2, _shift))
                    _shift += height + 15
                    self._updated.append((x, y, width, height))

                self._engine.show(self.surface, self._updated)
                self._before = self._focus
                self._updated = []

        except MenuQuit:
            pass

class MenuQuit(Exception):
    """Wyjście z menu."""

    pass

class MenuButton(object):
    """Pozycja w menu."""

    def __init__(self, _engine, text):
        """_engine - obiekt silnika, text - domyślny tekst przycisku."""

        super(MenuButton, self).__init__()
        self.text = text
        self.active = True
        self._engine = _engine

    def update(self):
        """Aktualizacja pozycji(zmiana tekstu/aktywności itp."""

        pass

    def callback(self):
        """Akcja przycisku."""

        pass

class ResolutionButton(MenuButton):
    """Przycisk do zmiany rozdzielczości."""

    def __init__(self, _engine):
        super(ResolutionButton, self).__init__(_engine, 'Rozdzielczosc: %dx%d' % _engine.getResolution())

    def callback(self):
        """Zmiana rozdzielczości i aktualizacja tekstu na przycisku."""

        self._engine.toggleResolution()
        self.text = 'Rozdzielczosc: %dx%d' % self._engine.getResolution()

class FullscreenButton(MenuButton):
    """Przycisk do zmiany trybu pełnoekranowego."""

    def __init__(self, _engine):
        super(FullscreenButton, self).__init__(_engine, _engine.getFullscreen() and 'Pelny Ekran' or 'Okno')

    def callback(self):
        """Zmiana trybu pełnoekranowego."""

        self._engine.toggleFullscreen()
        self.text = self._engine.getFullscreen() and 'Pelny ekran' or 'Okno'

class ExitButton(MenuButton):
    """Przycisk do wyjścia z gry."""

    def __init__(self, _engine):
        super(ExitButton, self).__init__(_engine, 'Wyjdz')

    def callback(self):
        """Zamykanie gry."""

        raise engine.EngineQuit()
