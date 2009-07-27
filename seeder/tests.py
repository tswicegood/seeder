from django.test import TestCase as DjangoTestCase
from seeder.models import *
from seeder.posters import TwitterPoster
from random import randint as random
from datetime import datetime
import time
import mox

def generate_random_authorized_account():
    u = User(username = "foo" + str(random(10000, 99999)))
    u.save()
    return AuthorizedAccount.objects.create(user = u)

def generate_random_seeder(account = None):
    if account is None:
        account = generate_random_authorized_account()
    return Seeder.objects.create(
        twitter_id = random(1000, 9999),
        authorized_for = account
    )

def generate_random_update(account = None):
    if account is None:
        account = generate_random_authorized_account()
    return Update.objects.create(
        posted_by = account,
        original_text = "Hello from Seeder!"
    )

class TestCase(DjangoTestCase):
    def tearDown(self):
        models = (AuthorizedAccount, Token, Seeder, Update, SeededUpdate,)
        for model in models:
            [obj.delete() for obj in model.objects.all()]


class TestOfSeededUpate(TestCase):
    def test_has_a_future_timestamp(self):
        foo = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update()
        )
        self.assertTrue(datetime.now() < foo.pub_date)

    def test_retrieves_updates_based_on_availability(self):
        first = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update(),
            pub_date = datetime.now()
        )

        second = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update(),
            pub_date = datetime.fromtimestamp(time.time() + 1)
        )

        self.assertEqual(1, len(SeededUpdate.objects.currently_available()))
        time.sleep(1.1)
        self.assertEqual(2, len(SeededUpdate.objects.currently_available()))

    def test_retrieves_updates_that_havenot_been_sent(self):
        first = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update(),
            pub_date = datetime.now()
        )
        second = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update(),
            pub_date = datetime.now()
        )

        self.assertEqual(2, len(SeededUpdate.objects.currently_available()))

        first.has_sent = 1;
        first.save()

        self.assertEqual(1, len(SeededUpdate.objects.currently_available()))

    def test_send_calls_on_poster(self):
        update = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update()
        )
        poster = mox.MockObject(TwitterPoster)
        poster.post(update)
        mox.Replay(poster)

        update.send(poster)

        mox.Verify(poster)


class TestOfUpdate(TestCase):
    def test_creates_seeded_updates_on_save(self):
        # sanity check
        self.assertEqual(0, len(SeededUpdate.objects.all()))

        a = generate_random_authorized_account()
        [generate_random_seeder(a) for i in range(10)]

        update = Update.objects.create(
            posted_by = a,
            original_text = "Hello from Seeder!"
        )

        self.assertEqual(10, len(SeededUpdate.objects.all()))

    def test_all_seeded_updates_have_random_pub_dates(self):
        a = generate_random_authorized_account()
        generate_random_seeder(a)

        update = Update.objects.create(
            posted_by = a,
            original_text = "Hello from Seeder!"
        )

        seeded_update = SeededUpdate.objects.get(update = update)

class TestOfAuthorizedAccount(TestCase):
    def test_at_water_returns_erins_account(self):
        at_water = AuthorizedAccount.objects.at_water()
        self.assertEqual("19673700", at_water.twitter_id)

