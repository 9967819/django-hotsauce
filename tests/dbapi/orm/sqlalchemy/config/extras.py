from notmm.utils.urlmap import RegexURLMap

urlpatterns = RegexURLMap()
urlpatterns.add_routes('', 
        #(r'^login/$', 'sandbox.views.login', {
        #    'template_name' : 'sandbox/login.mako'
        #}),

        # with_session decorator test
        (r'^test$', 'sandbox.views.test_session', {
            'template_name' : 'sandbox/test.mako'
        }),
        # with_schevo_database test
        (r'^test.schevo$', 'sandbox.views.test_schevo_database', {
            'template_name' : 'sandbox/test.mako'
        }),
        # handle302 test (Temporary redirects)
        (r'^moved/$', 'sandbox.handlers.handle302', {
            'location' : '/index.html'
        }),
        # handle500 test (sethandle)
        (r'^croak$', 'sandbox.views.croak')
)
urlpatterns.commit()

