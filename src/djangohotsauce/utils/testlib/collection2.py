"""TestCollection API

A bunch of functions and classes to extend on the ``unittest.TestLoader`` 
class for loading custom test collections. 

Test collections are regular directories to search for test scripts ::

    [app:myapp]
    collections = "fruits,vegetable,algae,mango"

"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import posixpath
import re
import sys

from djangohotsauce.utils.cutandpaste import colored as _

__all__ = (
    'get_base_dir',
    'get_test_modules',
    'is_test_script',
    'modfunc_noop',
    'test_script_re', 
    'TestCollection',
    'CollectionError'
    )

test_script_re = re.compile(r"test_\w+\.py$")

#logger = logging.getLogger(__name__)
#def _log(message):
#    logger.debug(message)    

# shortcut function to check if ``s`` is present in sys.path.
modfunc_noop = lambda s: bool(s in sys.modules)

_listoperator = lambda l: [item.strip() for item in l.rsplit(',')] 
_joinoperator = lambda a,b: posixpath.join(a, b)

class CollectionError(Exception):
    """An exception occured processing a test collection"""


def get_base_dir(dirname, _homedir='tests'):
    """Helper function to return a common prefix for test 
    scripts within the same directory structure.

    ``dirname``: Path to a directory holding test scripts.
    
    >>> get_base_dir('.')
    '.'
    >>> get_base_dir('dbapi/orm/elixir')
    'dbapi/orm/elixir'

    """
    #print dirname
    parts = dirname.rsplit('/', 1)
    if len(parts) >= 2:
        # return the last two components
        return os.path.join(parts[0], parts[-1])
    return parts[-1]


def is_test_script(pathname):
    """Determine if ``pathname`` is a test module and return True."""
    # For now, if its starting with prefix and
    # its ending with '.py' then return True.
    if isinstance(pathname, basestring) \
    and re.search(test_script_re, pathname):
        return True
    return False


def get_test_modules(collection, _topdown=False): 
    """Returns a sequence of usable test files (iterator)."""

    l = list()

    for item in _listoperator(collection):
        path = posixpath.realpath(item)
        if not os.path.exists(path):
            raise CollectionError("inexistent path: %r" % path)
        for dirname, names, files in os.walk(item, topdown=_topdown):
            basedir = get_base_dir(dirname)
            l.extend((# iterator start
                (_joinoperator(basedir, f), basedir) for f in files if is_test_script(f) 
                # iterator end
                ))
    return frozenset(l)

class TestCollection(unittest.TestLoader):
    """Helper class extending ``unittest.TestLoader``. 
    
    XXX: Put more documentation here.
    """
    
    def __init__(self, quiet=True, debug=0):
        super(TestCollection, self).__init__()
        self.quiet = quiet
        self.suite = unittest.TestSuite()
        self.interactive = False
        self.debug = debug

    def findTestCases(self, obj, 
        interactive=False, _TestCaseClass=unittest.TestCase):
        """
        Helper function to collect test cases inside a Python object
        or module. 
        """
        l = set()
        for item, value in obj.__dict__.items():
            if (item.endswith('TestCase') and \
            issubclass(value, _TestCaseClass)):
                # XXX Only attempt to filter test cases which belongs
                # to the test script
                try:
                    if interactive:
                        import pdb; pdb.set_trace()
                    testSuite = self.loadTestsFromTestCase(value)
                    #testCase = super(_TestCaseClass, value).__new__(*value.__bases__)
                    #_TestCaseClass.__init__(testCase)
                finally:
                    for testMethod in testSuite._tests:
                        #print "DEBUG: appending test method to test suite: %s" % testMethod
                        l.add(testMethod)
            #else:
            #    #print "ignored %s" % item
        
        return frozenset(l)

    def loadTestsFromNames(self, names, keep_going=False, interactive=False):
        """ Return a ``unittest.TestSuite`` object.

        This method can be used to create a custom test suite from 
        a list of user-defined test directories ::  

        .. coding: python

            >>> loader = TestCollection()
            >>> s2 = loader.loadTestsFromNames('apple,strawberry,pear')
        """
        tests = []
        for name in names:
            #relname = os.path.basename(name)[:-3] # remove the extension
            if not self.quiet: 
                _('Loading base=%r ...' % name)
            tests.append(
                self.discover(
                    os.path.realpath(name), top_level_dir=os.getcwd())
                    )
        self.suite.addTests(tests)
        #    self.suite.addTests(
        #        self.findTestCases(name, interactive=interactive)
        #        )
        #if self.debug > 1:
        #    print "[Testcases found: %d]" % self.suite.countTestCases()

        # Allow interactive debugging session if IPython is present
        #if len(resultset) >= 1:
        #    if not self.quiet:
        #        _("Found %d tests contained in %d modules." % (len(items), \
        #            len(names)))
        #        _("Total test cases count: %d." % suite.countTestCases())
        return self.suite

    loadTestsFromList = loadTestsFromNames
    
