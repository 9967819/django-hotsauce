=======================
 Django-hotsauce 0.5.3
=======================

- About_
- Features_
- License_

About
=======

Intro
-----

Welcome to the notmm toolkit, a open and accessible web
publishing platform on top of Django and WSGI.

Design philosophy
-----------------

**Scalable and non-monolithic By Design**

Allow developers to write scalable Django apps easily. The notmm toolkit
provides a modular API to develop reusable WSGI applications 
environment on top of the Django framework.

.. Also backward compatible with legacy Django apps (0.96.3) and Django (1.3).

**Pragmatic Web Application Development**

Allow developers to test and develop server side WSGI applications in 
a restricted environment by writing unit tests.

**Rapid Framework Refactoring**

Based on the ``unittest`` module for continuous integration and
rapid web framework refactoring. 

**Open Source**

Fully open source licensed (ISC). The notmm toolkit works best
under the Linux OS or a BSD variant. 

Features
========

- Follows the `WSGI`_ 1.0 specification for development of related HTTP-based libraries in Python.
- Supports most Django apps designed for Django, including Satchmo, FeinCMS, and more.
- MVC (``Model-View-Controller``) API design with built-in regular-expression URL dispatching.
- UTF-8 template loading, rendering, and caching. (`Mako`_, `Beaker`_ ``New``)
- Memcache backend support tools. (``New``)
- The API pages and the Developer Handbook are generated with `Doxygen`_ and `Sphinx`_ respectively. 
- Compatible with Python 2.5, 2.6, and 2.7. 
- Commercial support kindly offered and available on request. :)

Experimental Features
---------------------

- Experimental ``AES`` encryption of picklable Python objects using `pycryptopp`_
- Experimental `SQLAlchemy`_ database backends and functions. (Declarative mapper, `Elixir`_)
- Experimental non-relational database backends and functions. (`Schevo`_, `MongoDB`_)
- Experimental ``unittest2`` integration in the ``notmm.utils.test`` package. 
- Experimental ``I18N`` support. (Based on Django's I18N framework) 
- Experimental ``C bindings`` generation with `Cython`_. 

License
=======
Copyright 2007-2014 Etienne Robillard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

.. _WSGI: http://www.python.org/dev/peps/pep-0333/
.. _FastCGI: http://www.fastcgi.com/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Mako: http://www.makotemplates.org/
.. _Doxygen: http://www.stack.nl/~dimitri/doxygen/ 
.. _Elixir: http://elixir.ematia.de/trac/wiki/
.. _API pages: http://gthc.org/projects/notmm/refapi/
.. _Beaker: http://beaker.groovie.org/
.. _pycryptopp: http://allmydata.org/trac/pycryptopp/
.. _pickle: http://docs.python.org/library/pickle.html
.. _YAML: http://www.yaml.org/ 
.. _Schevo: http://www.schevo.org/
.. _MongoDB: http://www.mongodb.org/
.. _Cython: http://www.cython.org/
.. _Python: http://www.python.org/
.. _Django: http://www.djangoproject.org/
.. _DjangoBugfixes: https://gthc.org/wiki/DjangoBugfixes
.. _Sphinx: http://sphinx.pocoo.org/
.. _Developer Handbook: https://gthc.org/documentation/notmm/handbook/
