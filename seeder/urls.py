from django.conf.urls.defaults import url, patterns
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    'seeder.views',
    url(r'^(signup)?/?$', 'signup', name = 'seeder_signup'),
    url(r'^finish/?$', 'finish', name = 'seeder_finish'),
)

