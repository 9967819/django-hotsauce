import logging
import logging.handlers
logging.basicConfig(level=logging.WARNING)

syslogHandler =  logging.handlers.SysLogHandler(
        address="/dev/log", 
        facility=16)

