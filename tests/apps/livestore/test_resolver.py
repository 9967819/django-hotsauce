from notmm.utils.django_compat import reverse, RegexURLResolver
from notmm.utils.django_settings import LazySettings
settings = LazySettings()
urlconf = settings.ROOT_URLCONF
resolver = RegexURLResolver(r'^/', urlconf)
callback,args,kwargs = resolver.resolve('/store/')
print callback
