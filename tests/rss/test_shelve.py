#!/usr/bin/env python
import shelve
import feedcache

storage = shelve.open('.feeds_cache')

feedparser = feedcache.Cache(storage)
feed = feedparser.fetch('http://www.linuxinsight.com/rss.xml')
print type(feed)
