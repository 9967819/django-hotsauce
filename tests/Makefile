SHELL= /bin/sh
CURDIR=.
TOPDIR=$(CURDIR)
TESTDIR?=$(TOPDIR)

ENV?= /usr/bin/env
PYTHON?= python3
PYTHONFLAGS?= -W ignore
PYTHONPATH?= 
RM?= /bin/rm 
FIND?= find
TRUE?= true
MAKE?= gmake

ifdef WITH_PYPY
 PYTHON= pypy
endif

#List of options to override SimpleTestRunner invocation
OPTIONS?= devel #isotoperesearch

all: runtest
clean:
	$(FIND) $(CURDIR) -type f -name "*.py[co]" -exec $(RM) -rf '{}' ';' || $(TRUE)
runtest: clean
	$(CURDIR)/bin/runtest.sh ${OPTIONS} || $(TRUE)

PHONY: all clean runtest
