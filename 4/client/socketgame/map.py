# -*- encoding: utf8 -*-
# Maciej Szeptuch 2012

import pygame
import engine
import utils

## KIERUNKI

DIRECTION_NONE  = 1
DIRECTION_UP    = 2
DIRECTION_RIGHT = 4
DIRECTION_DOWN  = 8
DIRECTION_LEFT  = 16

## SZYBKOŚĆ PORUSZANIA MAPĄ

SLIDE_SPEED     = 15

class Map(object):
    """Wyświetlanie "mapy"."""

    def __init__(self, _engine, _scene, (_width, _height)):
        super(Map, self).__init__()
        self._engine = _engine
        self._scene = _scene
        self._shift = [0, 0]
        self._refresh = True
        self._size = 32 * _width, 32 * _height
        self.surface = pygame.Surface(self._size)
        self._ordered = []
        self._layers = {}
        self.addLayer('Background', -1, BackgroundLayer(self))
        self.screenUpdated()

    def getShift(self):
        """Zwraca przesunięcie mapy."""

        return tuple(self._shift)

    def getSize(self):
        """Zwraca szerokość i wysokość mapy(w px)."""

        return self._size

    def getRectangle(self):
        """Zwraca obszar zajmowany przez mapę."""

        return pygame.Rect(0, 0, self._resx, self._resy)

    def setShift(self, _shift):
        """Ustawia przesuniecie mapy."""

        _before = list(self._shift)
        if not self._holdpos[0]:
            self._shift[0] = _shift[0]

        if not self._holdpos[1]:
            self._shift[1] = _shift[1]

        self.move(DIRECTION_NONE)
        self._refresh = self._shift != _before

    def screenUpdated(self):
        """Aktualizuje wyświetlany obszar i w razie konieczności blokuje przesuwanie na osiach."""

        self._resx, self._resy = self._engine.getResolution()
        self._holdpos = [False, False]
        _mw, _mh = self.getSize()
        if self._resx > _mw:
            self._holdpos[0] = True
            self._shift[0] = (self._resx - _mw) / 2

        if self._resy > _mh:
            self._holdpos[1] = True
            self._shift[1] = (self._resy - _mh) / 2

        self._holdpos = tuple(self._holdpos)
        self._refresh = True

    def move(self, direction):
        """Przesuwa mapę."""

        _before = list(self._shift)
        _mw, _mh = self.getSize()
        if not self._holdpos[0]:
            if direction & DIRECTION_LEFT:
                self._shift[0] += SLIDE_SPEED

            elif direction & DIRECTION_RIGHT:
                self._shift[0] -= SLIDE_SPEED

            self._shift[0] = max(min(0, self._shift[0]), -_mw + self._resx)

        if not self._holdpos[1]:
            if direction & DIRECTION_UP:
                self._shift[1] += SLIDE_SPEED

            elif direction & DIRECTION_DOWN:
                self._shift[1] -= SLIDE_SPEED

            self._shift[1] = max(min(0, self._shift[1]), -_mh + self._resy)

        self._refresh = self._shift != _before

    def update(self):
        """Aktualizuje warstwy."""

        updated = []
        for layer, _ in self._ordered:
            updated.extend(map(lambda (x, y, w, h): pygame.Rect(x + self._shift[0], y + self._shift[1], w, h).clip(self.getRectangle()), layer.update()))
            layer.draw(self.surface, (-self._shift[0], -self._shift[1], self._resx, self._resy))

        if self._refresh:
            self._refresh = False
            return [self.getRectangle()]

        return updated

    def getLayer(self, _name):
        """Zwraca daną warstwę."""

        if _name in self._layers:
            return self._layers[_name][0]

        return None

    def removeLayer(self, _name):
        """Usuwa warstwę."""

        self._ordered.remove(self._layers[_name])
        del self._layers[_name]

    def addLayer(self, _name, _priority, _layer):
        """Dodaje warstwę."""

        self._layers[_name] = (_layer, _priority)
        _pos = 0
        while _pos < len(self._ordered):
            if self._ordered[_pos][1] > _priority:
                break

            _pos += 1

        self._ordered.insert(_pos, (_layer, _priority))

    def draw(self, surface):
        """Rysuje mape na powierzchni."""

        surface.blit(self.surface, (0, 0), (-self._shift[0], -self._shift[1], self._resx, self._resy))

class MapLayer(object):
    """Warstwa mapy."""

    def __init__(self, _map, _sprites = None):
        super(MapLayer, self).__init__()
        self._map = _map
        self.surface = pygame.Surface(_map.getSize(), pygame.SRCALPHA)
        self.hidden = False
        self._sprites = _sprites or pygame.sprite.Group()
        self._updated = []
        self._refresh = True
        self._check = True

    def update(self):
        """Aktualizuj elementy warstwy."""

        if self._refresh:
            self._refresh = False
            return [(0, 0) + self.surface.get_size()]

        updated = list(self._updated)
        self._updated = []
        for sprite in self._sprites:
            _upd = sprite.update()
            if _upd:
                updated.extend(_upd)
                sprite.draw(self.surface)

        if updated:
            self._check = True

        return updated

    def draw(self, _surface, rect = None):
        """Rysuj warstwę na powierzchni."""

        if not self.hidden:
            if not rect:
                _surface.blit(self.surface, (0, 0))

            else:
                _surface.blit(self.surface, rect, rect)

    def toggle(self):
        """Pokazuj/ukrywa warstwę."""

        self.hidden = not self.hidden

    def check(self):
        """Zwraca czy nastąpiły zmiany od ostatniego sprawdzenia."""

        _chk = self._check
        self._check = False
        return _chk

class BackgroundLayer(MapLayer):
    def __init__(self, _map):
        super(BackgroundLayer, self).__init__(_map, None)
        _image = utils.loadImage('gfx/tile.png')
        w, h = _map.getSize()
        for i in xrange(0, h / 32):
            for j in xrange(0, w / 32):
                self.surface.blit(_image, (j * 32, i * 32))

class ObjectsLayer(MapLayer):
    """Warstwa "wskaźników"."""

    def __init__(self, _map):
        super(ObjectsLayer, self).__init__(_map, None)
        self._repr = {}

    def move(self, _id, _pos):
        """Przesuwa wskaźnik _id do _pos."""

        self.clear(_id)
        _pos = _pos[0]*32 - 16, _pos[1]*32 - 16
        self._repr[_id].move(_pos)

    def add(self, _id, _sprite):
        """Dodaje sprite do wskaźników."""

        self._repr[_id] = _sprite
        self._sprites.add(_sprite)

    def remove(self, _id):
        """Usuwa sprite o _id ze wskaźników."""

        self._sprites.remove(self._repr[_id])
        self.clear(_id)
        del self._repr[_id]

    def get(self, _id):
        """Zwraca wskażnik _id."""

        if not _id in self._repr:
            return None

        return self._repr[_id]

    def clear(self, _id):
        """Usuwa obrazek _id z warstwy."""

        pygame.draw.rect(self.surface, (0, 0, 0, 0), self._repr[_id].rect)
        self._updated.append(tuple(self._repr[_id].rect))

    class Sprite(pygame.sprite.Sprite):
        """Podstawowy wskaźnik."""

        def __init__(self, _image = None):
            super(ObjectsLayer.Sprite, self).__init__()
            self.image = _image or pygame.Surface((0, 0))
            self.rect = self.image.get_rect()
            self._updated = []

        def kill(self):
            """Usuwa wskaźnik z warstwy."""

            super(ObjectsLayer.Sprite, self).kill()
            self.rect.center = (-1000, -1000)

        def getPos(self):
            return self.rect.center

        def changeImage(self, _image):
            """Ustawia nowy obrazek wskaźnika."""

            self.image = _image
            _pos = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = _pos
            self._updated.append(tuple(self.rect))

        def move(self, _pos):
            """Przesuwa wskaźnik w pozycje _pos."""

            self.rect.center = _pos
            self._updated.append(tuple(self.rect))

        def update(self):
            """Jeśli sprite się przesunął zwraca miejsce w którym się pojawi. Wpp []."""

            updated = list(self._updated)
            self._updated = []
            return updated

        def draw(self, surface, rect = None):
            """Rysuje sprite na powierzchni."""

            surface.blit(self.image, self.rect.topleft, rect)
