#!/usr/bin/env python

import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging
log = logging.getLogger('asyncio')
log.setLevel(logging.DEBUG)

from wsgiref import asyncio_server
from notmm.controllers.async import AsyncIOController
from notmm.utils.wsgilib import HTTPResponse, HTTPRequest

def start_loop(threads=4):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    assert threads >= 1, "threads should be >= 1"
    executor = ThreadPoolExecutor(threads)
    return loop, executor

@asyncio.coroutine
def helloworld(environ, start_response):
    return (yield from HTTPResponse("hello world")(environ, start_response))

@asyncio.coroutine
def application(environ, start_response):
    request = HTTPRequest(environ)
    try:
        result = (yield from AsyncIOController()(environ, start_response))
    except:
        raise
    else:
        yield from result

if __name__ == '__main__':
    loop, executor = start_loop()
    
    server = asyncio_server.make_server('127.0.0.1', 8000, application)
    loop.run_in_executor(executor, server.serve_forever())

