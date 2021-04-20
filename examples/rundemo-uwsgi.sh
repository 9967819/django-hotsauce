#!/bin/bash
set -x
#For production:
#/usr/bin/uwsgi --socket localhost:8000 --wsgi-file test_basic.py 
source ./djangorc
/usr/bin/uwsgi --http-socket localhost:8000 --wsgi-file standalone/standalone-asyncio.py
