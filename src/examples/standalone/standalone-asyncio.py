#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ASyncIOController demo

"""
import asyncio
from notmm.utils.django_settings import LazySettings
from notmm.controllers.async import AsyncIOController
    
@asyncio.coroutine
def application(environ, start_response):

    settings = LazySettings()

    result = (yield from AsyncIOController(settings=settings)(environ, start_response))
    
    yield from result



    
