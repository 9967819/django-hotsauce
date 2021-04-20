import os.path
from notmm.utils.urlmap import RegexURLMap

from django.contrib import admin
admin.autodiscover()

urlpatterns = RegexURLMap()
urlpatterns.add_routes('',
    (r'^$', 'localsite.views.example', {})
    )
urlpatterns.add_routes('',    
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(os.path.dirname(__file__), 'media/')})
    )

urlpatterns.include(admin.site.urls, prefix='^admin/')
