#!/usr/bin/env python
from notmm.utils.configparse import setup_all, is_equal
import logging_conf

global_conf = {}

setup_all('sandbox', global_conf)
#setup_all('logging', global_conf)# logging options

#logconf = global_conf['logging']
#if is_equal(logconf['enabled'], 'true'):
#    logger = getattr(logging_conf, 'logger_func')
#    logger('Logging subsystem started!')
#print global_conf['logging']
