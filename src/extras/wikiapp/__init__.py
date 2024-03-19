#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from notmm.utils.configparse import setup_all
global_conf = dict()
setup_all(__name__, global_conf)
setup_all('httpserver', global_conf) # add httpserver support
#print global_conf[__name__]

from wikiapp.controllers import MoinMoinController

try:
    default_instance = global_conf[__name__].get('default_instance')
except KeyError:
    default_instance = None

