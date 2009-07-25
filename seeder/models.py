from django.db import models

class AuthorizedTwitter(models.Model):
    user_id = models.CharField(max_length = 100)

class Token(models.Model):
    user_id = models.CharField(max_length = 100)
    oauth_token = models.CharField(max_length = 100)
    oauth_token_secret = models.CharField(max_length = 100)

class Seeder(models.Model):
    user_id = models.CharField(max_length = 100)
    authorized_for_user_id = models.ForeignKey(AuthorizedTwitter)

class Update(models.Model):
    posted_by = models.ForeignKey(AuthorizedTwitter)
    original_text = models.CharField(max_length = 140)
    pub_date = models.DateTimeField(auto_now_add = True)

class SeededUpdates(models.Model):
    seeder = models.ForeignKey(Seeder)
    update = models.ForeignKey(Update)
    has_sent = models.BooleanField()

