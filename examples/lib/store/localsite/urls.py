from notmm.utils.urlmap import RegexURLMap
from django.conf.urls import url
from store.localsite import views

urlpatterns = RegexURLMap()

urlpatterns.add_routes('',
    url(r'example/', views.example, {}),
)
