#!/bin/sh
# rundemo.sh 
# Starts a demo WSGI application in Django maintainer mode.

# for debugging
set -x
# raise system ulimits (max open files)
#ulimits -n 1024

# magic command to set appropriate ROOTDIR variable
ROOTDIR=`cd -P -- "$(dirname -- "$0")/.." && pwd -P`

# the location where this script is held
VENDORDIR="$ROOTDIR/examples"

# location of global configuration files 
SYSCONFDIR="$VENDORDIR/conf"
CONTRIBDIR="$VENDORDIR/contrib"

LIBDIR="$VENDORDIR/lib:$VENDORDIR/lib/site-packages"
PYTHONPATH="$VENDORDIR:$CONTRIBDIR:$LIBDIR:$DJANGO_HOME"; export PYTHONPATH
#set default python interpreter to /usr/local/bin/pypy here
PYTHON=/usr/bin/python2.7

# 
#if -z "$DJANGO_SETTINGS_MODULE"; then
#    export DJANGO_SETTINGS_MODULE=local_settings
#fi
export DJANGO_SETTINGS_MODULE='helloworld.config.settings'

runserv() {
local err=3
while test "$err" -eq 3 ; do
 ${PYTHON} ${ROOTDIR}/tools/httpserver.py \
 -d \
 -c "$SYSCONFDIR/debug.ini" \
 --disable-auth --settings="$DJANGO_SETTINGS_MODULE" --wsgi-app=helloworld.wsgi.application $@
 err="$?"
done 
}
echo "Starting up Django in maintainer mode..."
runserv $@
