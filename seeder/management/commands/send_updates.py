from django.core.management.base import BaseCommand
from seeder.models import SeededUpdate
from seeder.posters import TwitterPoster


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        poster = TwitterPoster()
        updates = SeededUpdate.objects.currently_available()
        [update.send(poster) for update in updates]

