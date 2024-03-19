"""Helper functions mostly useful for web applications testing.
"""
import sys, os

from .collection2 import TestCollection, unittest

__all__ = ('SimpleTestRunner', )

class SimpleTestRunner(unittest.TextTestRunner):
    """
    A simplified ``unittest.TextTestRunner`` subclass with 
    RFC-822 style configuration.
    """
    
    #config_options = ('collections', 'exclude', 'quiet', 'extra_libs')
    defaults = {'quiet' : True}

    def __init__(self, namespace, verbosity=1, 
        keep_going=False, interactive=False):
        """Setup default options for the TestRunner object. 
        
        XXX: Put more documentation here.
        """
        self.quiet = self.defaults['quiet']

        if int(verbosity) >= 2:
            self.quiet = False

        self.app_conf = namespace.app_conf
        self.collections = namespace.collections
        self.vpath = namespace.vpath
        self.verbosity = int(verbosity)
        self.keep_going = keep_going
        self.interactive = bool(interactive)

        # add any extra paths to sys.path
        if self.vpath is not None:
            sys.path.extend([dirname for dirname in self.vpath if \
                os.path.exists(dirname) ])


    def __call__(self, **kwargs):
        """Invokes the ``run`` method. """
        return self.run(**kwargs)

    def run(self, **kwargs):
        """Run the test-suite using ``TextTestRunner``"""

        loader = TestCollection(quiet=self.quiet, debug=self.verbosity)
        suite = loader.loadTestsFromNames(self.collections, 
            keep_going=self.keep_going,
            interactive=self.interactive
            )
        unittest.TextTestRunner(verbosity=self.verbosity).run(suite)

