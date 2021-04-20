# Django Signals Ahoy
# Copyright Bruce Kroeze 2009
#
# Released under the "New BSD License"
# Please see LICENSE.rst in this distribution for license details.
# -----------------
"""
Useful signals:

 - `application_search`: sent by search views to ask all listeners to add search results::

    Ex: application_search.send(Sender, request=request, keywords=keywords, results={})

 - `collect_urls`: sent by urls modules to allow listeners to add urls to that module::

    Ex: collect_urls.send(sender=MODULE, patterns=urlpatterns)

- `form_initialdata`: sent by forms when collecting initial data::

    Ex: form_initialdata.send(sender=FORM, initial={}, [arg=val, arg2=val2, ...])

 - `form_init`: sent by forms when adding fields::

    Ex: form_init.send(sender=FORM, [arg=val, arg2=val2, ...])

 - `form_presave`: sent by forms just prior to saving::

    Ex: form_presave.send(sender=FORM, [arg=val, arg2=val2, ...])

 - `form_postsave`: sent by forms just after saving::

    Ex: form_postsave.send(sender=FORM, [arg=val, arg2=val2, ...])
    
- `form_validate`: sent by forms prior to validation::

    Ex: form_validate.send(sender=FORM, form=FORM)

 - `view_prerender`: sent by views just before rendering::

    Ex: view_prerender.send(sender=VIEW, context=CONTEXT)

"""
import django.dispatch
application_search = django.dispatch.Signal()
collect_urls = django.dispatch.Signal()
form_init = django.dispatch.Signal()
form_initialdata = django.dispatch.Signal()
form_presave = django.dispatch.Signal()
form_postsave = django.dispatch.Signal()
form_validate = django.dispatch.Signal()
view_prerender = django.dispatch.Signal()
