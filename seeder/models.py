from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime
from time import time
from random import randint as random

SECONDS_IN_A_DAY = 60 * 60 * 24
THIRTY_DAYS = SECONDS_IN_A_DAY * 30

class AuthorizedAccountManager(models.Manager):
    def default_account(self):
        return self.filter(twitter_id = settings.SEEDER['default_twitter_id'])[0]

class AuthorizedAccount(models.Model):
    user = models.ForeignKey(User)
    twitter_id = models.CharField(max_length = 100, blank = True, null = True)
    facebook_id = models.CharField(max_length = 100, blank = True, null = True)

    objects = AuthorizedAccountManager()

    def __unicode__(self):
        return self.user.get_full_name()

class Seeder(models.Model):
    twitter_id = models.CharField(max_length = 100)
    twitter_username = models.CharField(max_length = 100)
    authorized_for = models.ForeignKey(AuthorizedAccount)
    expires_on = models.DateTimeField()

    def __unicode__(self):
        return self.twitter_username

    def save(self, *args, **kwargs):
        if self.expires_on is None:
            self.set_expires_on_in_days(30)
        super(Seeder, self).save(*args, **kwargs)

    def set_expires_on_in_days(self, days):
        self.expires_on = datetime.fromtimestamp(time() + (SECONDS_IN_A_DAY * int(days)))

class Token(models.Model):
    seeder = models.ForeignKey(Seeder)
    oauth_token = models.CharField(max_length = 100)
    oauth_token_secret = models.CharField(max_length = 100)

class Update(models.Model):
    posted_by = models.ForeignKey(AuthorizedAccount)
    original_text = models.CharField(max_length = 140)
    pub_date = models.DateTimeField(auto_now_add = True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super(Update, self).save(*args, **kwargs)

        if is_new is False:
            return;

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
        self.has_sent = True
        self.save()


