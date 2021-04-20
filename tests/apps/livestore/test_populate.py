from notmm.utils.django_compat import resolve
from notmm.utils.django_settings import LazySettings
settings = LazySettings()
urlconf = settings.ROOT_URLCONF
url = resolve('/store/', urlconf=urlconf)
print url
url = resolve('/admin/product/1/')
print url
#url = resolve('/admin/auth/user/2/')
#print url
