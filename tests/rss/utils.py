#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import shelve
import feedcache
import socket
#socket.setdefaulttimeout(10)
from xml.sax._exceptions import SAXException

_MEMSTORE='/var/db/feeds/feed_cache'

feed_store = shelve.open(_MEMSTORE)

__all__ = ['get_feed_choices', 'get_feed', 'feed_store']

def get_feed_choices(delimiter=';'):
    """
    Parses a CSV formatted file and returns a dictionary mapping of
    valid feed choices. -> (key_id, url)
    """
    data = {}
    # first get the csv data
    fixture_dir = os.path.join(
        os.path.dirname(__file__), 'fixtures')
    fp = open(os.path.join(fixture_dir, 'feeds.txt'))
    reader = csv.reader(fp, quoting=csv.QUOTE_NONE, delimiter=delimiter)
    for row in reader:
        data[row[1]] = row[0]
    
    return data


def get_feed(feed_id, limit=10):
    


    feed_store['feed_choices'] = get_feed_choices()
    parser = feedcache.Cache(feed_store)

    try:
        feed_choices = feed_store['feed_choices']
        feed = parser.fetch(feed_choices[feed_id], force_update=True)

    except (SAXException, KeyError, socket.error):
        # Invalid feed
        # print 'buggy feed detected: %s' % feed_id
        raise
    
    # Never fetch more than MAX_ITEMS entries
    feed.entries = [item for item in feed.entries][:limit]
    return feed


if __name__ == '__main__':
    lst = get_feed_choices()
    print "%d valid feeds found" % len(lst)
    print lst
    
