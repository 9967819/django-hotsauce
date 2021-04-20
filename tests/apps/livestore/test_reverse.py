from notmm.utils.django_compat import reverse
from notmm.utils.django_settings import LazySettings
settings = LazySettings()
urlconf = settings.ROOT_URLCONF
url = reverse('satchmo_category', urlconf=urlconf, kwargs={'slug' : 'softwares'})

print url

url = reverse('satchmo_search')
print url

url = reverse('satchmo_shop_home')
print url
