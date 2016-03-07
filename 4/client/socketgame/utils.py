# -*- encoding: utf8 -*-
# Maciej Szeptuch

import os
from collections import defaultdict
import pygame

## BUFOR CZCIONEK
FONTS = {}

## BUFOR OBRAZKÓW
IMAGES = {}

## BUFOR DŹWIĘKÓW
SOUNDS = {}

class NoSound:
    """Obiekt reprezentujący brak dźwięku."""

    def play(self, *args): pass
    def stop(self, *args): pass
    def fadeout(self, *args): pass

def dictfactory():
    """Nieskończony słownik."""

    return defaultdict(dictfactory)

def raise_(exception):
    """Rzucanie wyjątku w formie funkcji. Przydatne do lambd."""

    raise exception

def loadImage(path, transparency = None, alpha = False):
    """Wczytywanie obrazka dla pygame."""

    path = os.path.join(os.path.dirname(__file__), path)
    _id = path + ':' + str(transparency) + ':' + str(alpha)
    if IMAGES.has_key(_id):
        return IMAGES[_id]

    try:
        image = pygame.image.load(path)
        if alpha:
            image = image.convert_alpha()

        else:
            image = image.convert()

    except pygame.error, msg:
        print 'WARNING:', path, msg
        return None

    if transparency != None:
        if transparency == -1:
            transparency = image.get_at((0, 0))

        image.set_colorkey(transparency, pygame.RLEACCEL)

    IMAGES[_id] = image
    return image

def loadImages(directory, transparency = None, alpha = False):
    """Wczytywanie obrazków z folderu do słownika."""

    images = dictfactory()
    for path, _, files in os.walk(directory):
        if not files:
            continue

        act = images
        for name in path.replace(directory, '').split('/'):
            if name:
                act = act[name]

        for filename in files:
            name = os.path.splitext(filename)[0]
            act[name] = loadImage(os.path.join(path, filename), transparency,
                    alpha)

            return images

def loadSound(path):
    """Wczytuje dźwięk dla pygame."""

    if SOUNDS.has_key(path):
        return SOUNDS[path]

    if not os.path.exists(path):
        print 'WARNING:', path
        return NoSound()

    SOUNDS[path] = pygame.mixer.Sound(path)
    return SOUNDS[path]

def drawText(surface, text, size, color, (x, y), antialiasing = True):
    """Wypisuje tekst na ekranie, wyśrodkowany w pkt. (x, y)."""
    if not size in FONTS:
        FONTS[size] = pygame.font.Font(pygame.font.get_default_font(), size)

    renders = []
    width = 0
    height = 0
    for line in text.split("\n"):
        render = FONTS[size].render(line, antialiasing, color)
        renders.append(render)
        w, h = render.get_size()
        width = max(width, w)
        height += h

    act = 0
    for render in renders:
        w, h = render.get_size()
        surface.blit(render, (x - w / 2, y - height / 2 + act))
        act += h

    return x - width / 2, y - height / 2, width, height
