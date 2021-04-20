"""Urls which need to be loaded at root level."""
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^admin/product/configurableproduct/(?P<id>\d+)/getoptions/', 
        'product.views.get_configurable_product_options', {}, 
        'configurableproduct'),
)

urlpatterns += patterns('product.views.adminviews',
    (r'^admin/inventory/edit/$', 
        'edit_inventory', {}, 'edit_inventory'),
    (r'^inventory/export/$',
        'export_products', {}, 'product_export'),
    (r'^inventory/import/$', 
        'import_products', {}, 'product_import'),
    # (r'^inventory/report/$', 
    #     'product_active_report', {}, 'satchmo_admin_product_report'),
    (r'^admin/(?P<product_id>\d+)/variations/$', 
        'variation_manager', {}, 'variation_manager'),
    (r'^admin/variations/$', 
        'variation_list', {}, 'variation_list'),
)
