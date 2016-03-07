#!/usr/bin/env python2
# -*- encoding: utf-8 -*-
from distutils.core import setup
from socketserver import version

setup(
    name = 'socketserver',
    version = version,
    author = 'Maciej Szeptuch',
    author_email = 'neverous@neverous.info',
    packages = ['socketserver'],
    scripts = ['bin/socketserver', 'bin/server-ctl'],
    description = 'Serwer do gry na Kurs Pythona 2012/2013, napisany z użyciem twisted.',
    url = 'http://example.com',
    requires = [
        'twisted (>= 12.3.0)',
        'protocolObjects (>= 1.0.0)',
    ],
)
