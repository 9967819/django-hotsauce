#!/bin/sh
# Copyright (C) 2010 Etienne Robillard <erob@gthcfoundation.org>
# All rights reserved.
 

# Enable this option if you're debugging the script
# itself.
set -x

PATH="/bin:/usr/bin:/usr/local/bin"
PYTHONIOENCODING="UTF-8"
PYTHON=/usr/bin/python
IPYTHON=`which ipython`
FIND=/usr/bin/find
HTTPSERVER=/usr/local/bin/httpserver.py

### Root dir
ROOTDIR=`cd -P -- "$(dirname -- "$0")/.." && pwd -P`
### Directory where internal libraries are found
LIBDIR="$ROOTDIR/lib"
### Directory where scripts are found
BINDIR="$ROOTDIR/bin"
### Third-party Python modules 
VENDORDIR="$ROOTDIR/contrib"

SYSCONFDIR="$ROOTDIR/conf"

### Required for backward-compatibility
### DJANGO_SETTINGS_MODULE='local_settings'

# Set DJANGO_HOME unless its already provided
if test -z "$DJANGO_HOME" ; then
 echo "WARNING: DJANGO_HOME not found, using default"
 export DJANGO_HOME="$VENDORDIR"
fi

### setup PYTHONPATH
PYTHONPATH="$ROOTDIR:$LIBDIR:$DJANGO_HOME:$VENDORDIR:$SYSCONFDIR"

export PATH PYTHONIOENCODING PYTHONPATH ROOTDIR 
export SCHEVO_OPTIMIZE=1

clean() {
    # ensure that we start clean
    $FIND $ROOTDIR -name "*.py[co]" -exec rm -f '{}' ";" || true
    $FIND $ROOTDIR -name "*.sw[po]" -exec rm -f '{}' ";" || true
    # clean up memcache..
    [ -x "$BINDIR/cleanMemcache.py" ] && $PYTHON $BINDIR/cleanMemcache.py
}
manage() {
    shift;
    $PYTHON $BINDIR/manage.py $@
}
#create_user() {
#    shift;
#    python $BINDIR/create_user.py $@
#}
daemonize() {
    shift;
    $PYTHON $BINDIR/daemonize.py $@;
}    
runserver() {
    local err=3
    while test "$err" -eq 3 ; do
        #shift;
        $PYTHON $HTTPSERVER -d -c $ROOTDIR/development.ini --settings=$DJANGO_SETTINGS_MODULE
        err="$?"
    done
}
respawn(){
    shift;
    eval "$BINDIR/respawn.sh" "$@"
}
moinmoin_start(){
    shift;
    eval "$BINDIR/moinmoin.sh" "$@"
} 
comment_manager_start(){
    shift;
    eval "$PYTHON $BINDIR/CommentManager.py $@";
}
upgradedb(){
    shift;
    eval "$BINDIR/upgradedb.sh" "$@";
}
syncdb(){
    shift;
    eval "$BINDIR/syncdb.sh" "$@";
}    
shell(){
    # start a shell (ipython) 
    shift;
    if test -x "$IPYTHON"; then
     $IPYTHON "$@"
    else
     echo 'Please install IPython.'
     exit 2
    fi;     
}
create_sitemap(){
    # recreate the sitemap.xml file
    shift;
    eval "$PYTHON $BINDIR/create_sitemap.py" "$@";
}

case $1 in manage)
    manage "$@"
    ;; 
clean)
    clean
    ;;
create_sitemap)
    create_sitemap "$@"
    ;;
daemonize)
    daemonize "$@"
    ;;
respawn)
    #clean;
    respawn "$@"
    ;;
runserver)
    clean; # start clean
    runserver "$@"
    ;;
moinmoin)
    clean;
    moinmoin_start "$@"
    ;;
manage_comments)
    clean;
    comment_manager_start "$@"
    ;;
upgradedb)
    upgradedb "$@"
    ;;
syncdb)
    syncdb "$@"
    ;;
shell)
    shell "$@"
    ;;
*)
    #echo "Usage: debug.sh <clean|manage|respawn|runserver|moinmoin> [options]"
    echo "Usage: $0 <command> [options]"
    echo "Available commands: clean, manage, respawn, runserver, moinmoin,
	manage_comments, upgradedb"

    exit 0;
esac        
