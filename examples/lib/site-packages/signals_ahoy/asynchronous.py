# Django Signals Ahoy
# Copyright Bruce Kroeze 2009
#
# Released under the "New BSD License"
# Please see LICENSE.rst in this distribution for license details.
# -----------------
import threading
import logging

log = logging.getLogger('signals_ahoy.asynchronous')

class AsynchronousListener(object):
    """A wrapper for signal listeners which will run the listen function in a separate thread."""
    
    def __init__(self, listenfunction, label="Anonymous"):
        self.listenfunction = listenfunction
        self.label = "label"
        
    def listen(self, *args, **kwargs):
        log.debug('asynclistener starting runner: %s', self.label)
        listener = AsynchronousRunner(self.listenfunction, *args, **kwargs)
        listener.start()

class AsynchronousRunner(threading.Thread):
    def __init__(self, listenfunction, *args, **kwargs):
        super(AsynchronousRunner, self).__init__()
        self.listenfunction = listenfunction
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        self.listenfunction(*self.args, **self.kwargs)
