#!/usr/bin/env python
"""Basic logging utilities"""
import sys, os
import logging
import logging.handlers

__all__ = ['configure_logging']

def configure_logging(logger, level=logging.DEBUG, 
    error_log='/var/log/django.log', enable_syslog=True):
    
    logger = logging.getLogger(logger)
    logger.setLevel(level)
    
    if enable_syslog:
        syslog_handler = logging.handlers.SysLogHandler('/dev/log')
        logger.addHandler(syslog_handler)

    default_handler = logging.FileHandler(error_log)
    logger.addHandler(default_handler)
    return logger

