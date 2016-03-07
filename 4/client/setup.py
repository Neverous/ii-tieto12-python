#!/usr/bin/env python2
# -*- encoding: utf-8 -*-
from distutils.core import setup
from socketgame import version

setup(
    name = 'socketgame',
    version = version,
    author = 'Maciej Szeptuch',
    author_email = 'neverous@neverous.info',
    packages = ['socketgame'],
    scripts = ['bin/socketgame'],
    package_dir = {'socketgame': 'socketgame'},
    package_data = {'socketgame': ['gfx/*.png', 'gfx/*.jpg', 'gfx/hero/*']},
    description = 'Klient do gry na Kurs Pythona 2012/2013, napisany z użyciem twisted i pygame.',
    url = 'http://example.com',
    requires = [
        'twisted (>= 12.3.0)',
        'pygame (>= 1.9.1)',
        'protocolObjects (>= 1.0.0)',
    ],
)
