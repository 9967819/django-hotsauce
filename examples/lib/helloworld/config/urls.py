#!/usr/bin/env python
# -*- coding: utf-8 -*-

from notmm.utils.urlmap import RegexURLMap, url, include
from notmm.release import VERSION
from notmm.utils.django_settings import LazySettings

from helloworld.forms import LoginForm
from helloworld.login_views import login, logout
settings = LazySettings()
render_to_response = 'notmm.utils.template.direct_to_template'

extra_context = {
    #'settings': settings,
    'local_version': VERSION,
    'media_url': settings.MEDIA_URL 
}

#import pdb; pdb.set_trace()
urlpatterns = RegexURLMap()

urlpatterns.add_routes('',   
   url(r'(?P<path>\w+.(gif|png|jpg|ico))$', \
    'helloworld.views.image_handler', {
        'document_root' : settings.MEDIA_ROOT }
   ),
)

urlpatterns.add_routes('',
   # Frontdoor (a simple generic view)
   url(r'^$|index.html$', render_to_response, {
        'template_name': 'default/index.mako',
        'extra_context': extra_context
   }),
   #url(r'^authorize/', include('oauth2_provider.urls'))
   url(r'^session_login/$', login),
   url(r'^session_logout/$', logout)
   )
#urlpatterns.commit()
#print len(urlpatterns)
