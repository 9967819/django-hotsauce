from django.contrib.sites.models import SiteManager, Site
from threaded_multihost import sites

def site_get_current(self):
    """Overridden version of get_current, which is multihost aware."""
    return sites.by_host()

SiteManager.get_current = site_get_current
SiteManager.MULTIHOST = True
