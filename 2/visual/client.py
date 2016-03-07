#!/usr/bin/python2
# -*- encoding: utf8 -*-
# Maciej Szeptuch 2012

import sys
import pygame
import version
sys.path.append('./data')
sys.path.append('../')
import engine
from menu import Menu, ResolutionButton, FullscreenButton, ExitButton
from scene import NewGameButton
import utils
import logging

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG)
    if len(sys.argv) < 3:
        raise AttributeError("Incorrect number of arguments. You should pass ip:port as argument.")

    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption(version.NAME + ' v' + version.VERSION)
    _engine = engine.Engine((sys.argv[1], sys.argv[2]), len(sys.argv) > 3 and sys.argv[3] == '--debug') # --debug aby włączyć tryb testowy(pokazuje które części ekranu się odświeżają)
    _engine.addModule(Menu(_engine, (
        NewGameButton(_engine), # Nowa gra
        ResolutionButton(_engine), # Rozdzielczosc
        FullscreenButton(_engine), # Pelny ekran/okno
        ExitButton(_engine), # Wyjscie
    )))
    _engine.activateModule('Menu')
    try:
        _engine.run()

    except KeyboardInterrupt:
        pass
