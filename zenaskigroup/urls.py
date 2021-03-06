# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls import *  # NOQA
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from zenaskigroup.utils import EmailValidationOnForgotPassword

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'', include('trips.urls')),

    url(r'^accounts/password/reset/$',
        'django.contrib.auth.views.password_reset',
        { 'post_reset_redirect': '/accounts/password/reset/done/',
         'html_email_template_name': 'registration/password_reset_email.html',
         'password_reset_form': EmailValidationOnForgotPassword},
        name="password_reset"),

    url(r'^admin/', include(admin.site.urls)),  # NOQA
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': {'cmspages': CMSSitemap}}),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^', include('cms.urls')),
)

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        ) + staticfiles_urlpatterns() + urlpatterns  # NOQA
