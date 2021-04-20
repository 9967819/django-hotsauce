#!/usr/bin/env python
# -*- coding: utf-8 -*-


from notmm.utils.YAMLDct import RandomYAMLDct
#from mainapp.feeds.utils import get_feed

#def settings(request):
#    ctx = dict(settings=_settings)
#    return ctx

def request(request):
    ctx = dict(request=request)
    return ctx

def link_set(request):
    # custom links to put on every pages
    default_set =  RandomYAMLDct('lib/mainapp/static/content/1/free-software.yaml')

    dct = {
        'free_software' : default_set
        #'blogs-fr': YAMLDct('blogs-fr.yaml'),
        #'opendata': YAMLDct('opendata.yaml'),
        #'notmm-api': YAMLDct('notmm-api.yaml', randomized=False),
        #'webmaster-tools': YAMLDct('webmaster-tools.yaml'),
        #'truth-alliance': YAMLDct('truth-alliance.yaml')
        #'for-sale': YAMLDct('for-sale.yaml') ## livestore links!
    }
    return {'link_set' : dct}

#def rss(request):
#    dct = {
#        'rss' : get_feed('django-hotsauce')
#    }
#    return dct

