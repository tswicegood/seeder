from django.contrib import admin
from seeder.models import AuthorizedAccount, Seeder, Update

admin.site.register(AuthorizedAccount)
admin.site.register(Seeder)
admin.site.register(Update)
