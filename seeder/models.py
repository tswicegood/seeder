from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from time import time
from random import randint as random

class AuthorizedAccount(models.Model):
    user = models.ForeignKey(User)
    twitter_id = models.CharField(max_length = 100, blank = True, null = True)
    facebook_id = models.CharField(max_length = 100, blank = True, null = True)

class Token(models.Model):
    user_id = models.CharField(max_length = 100)
    oauth_token = models.CharField(max_length = 100)
    oauth_token_secret = models.CharField(max_length = 100)

class Seeder(models.Model):
    user_id = models.CharField(max_length = 100)
    authorized_for = models.ForeignKey(AuthorizedAccount)

class Update(models.Model):
    posted_by = models.ForeignKey(AuthorizedAccount)
    original_text = models.CharField(max_length = 140)
    pub_date = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        super(Update, self).save(*args, **kwargs)
        # TODO: queue these up instead of doing them all at save
        for seeder in self.posted_by.seeder_set.all():
            s = SeededUpdate.objects.create(
                seeder = seeder,
                update = self
            )

class SeededUpdateManager(models.Manager):
    def currently_available(self):
        return self.filter(pub_date__lte = datetime.now(), has_sent = False)

class SeededUpdate(models.Model):
    seeder = models.ForeignKey(Seeder)
    update = models.ForeignKey(Update)
    has_sent = models.BooleanField(default = False)
    pub_date = models.DateTimeField()

    objects = SeededUpdateManager()

    def save(self, *args, **kwargs):
        if self.pub_date is None:
            self.pub_date = datetime.fromtimestamp(time() + random(60, 60 * 30))
        super(SeededUpdate, self).save(*args, **kwargs)

    def send(self, poster):
        poster.post(self)


