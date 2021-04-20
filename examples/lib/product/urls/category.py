from notmm.utils.urlmap import RegexURLMap, url

urlpatterns = RegexURLMap(label='Product category urlconf')
urlpatterns.add_routes('product.views',
    url(r'^(?P<parent_slugs>([-\w]+/)*)(?P<slug>[-\w]+)/$', 
        'category_view', {}, name='satchmo_category'),
    url(r'^$', 'category_index', {}, name='satchmo_category_index'),
)
