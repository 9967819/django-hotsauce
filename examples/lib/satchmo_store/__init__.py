import os
import logging
#import django
#django.setup()
from django.conf import settings

VERSION = "1.0"

def configureLogging(level='debug'):
    logging_level_choices = {
        'error' : logging.ERROR,
        'debug' : logging.DEBUG,
        'info'  : logging.INFO,
        'critical'  : logging.CRITICAL,
    }
    loglevel = logging_level_choices[level]
    logfile = os.path.join(settings.SATCHMO_LOGDIR, 'satchmo.log')

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
    filename=logfile,
    filemode='w')

    logging.getLogger('keyedcache').setLevel(loglevel)
    logging.getLogger('l10n').setLevel(loglevel)
    
    logging.info("Satchmo Logging subsystem initialized.")
    print "Sending log messages to %s" % logfile
    
    return None

