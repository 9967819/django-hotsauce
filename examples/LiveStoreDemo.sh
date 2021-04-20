#!/bin/sh
# A simple Satchmo-based store app (demo version) 
# Copyright (C) 2010 Etienne Robillard <erob@gthcfoundation.org>
# All rights reserved.
#
#
set -x
ROOTDIR="$(pwd)"
SATCHMO_ROOTDIR="$ROOTDIR"; export SATCHMO_ROOTDIR
CONTRIBDIR="$ROOTDIR/contrib"
LIBDIR="$ROOTDIR/lib"
#DJANGO_SETTINGS_MODULE="local_settings"; export DJANGO_SETTINGS_MODULE
PYTHONPATH="$PYTHONPATH:$ROOTDIR:$LIBDIR:$DJANGO_HOME"; export PYTHONPATH
err=3
while test "$err" -eq 3 ; do
 /usr/bin/python -Wonce ../tools/httpserver.py -d -c "$ROOTDIR/conf/satchmo_conf.ini" --disable-auth --enable-django-setup --settings="satchmo_store.conf.defaults" "$@"
 err="$?"
done 
