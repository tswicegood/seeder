from django.test import TestCase as DjangoTestCase
from django.conf import settings
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

def generate_mock_poster(update):
    poster = mox.MockObject(TwitterPoster)
    poster.post(update)
    mox.Replay(poster)
    return poster

class TestCase(DjangoTestCase):
    def assertPubDateBetween(self, obj, begin, end):
        self.assertTrue(obj.pub_date > begin and obj.pub_date < end)

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
        poster = generate_mock_poster(update)
        update.send(poster)

        mox.Verify(poster)

    def test_send_marks_updates_as_sent(self):
        update = SeededUpdate.objects.create(
            seeder = generate_random_seeder(),
            update = generate_random_update(),
            pub_date = datetime.now()
        )

        self.assertEqual(len(SeededUpdate.objects.currently_available()), 1,
            "sanity check to ensure value seeded update is present")
        update.send(generate_mock_poster(update))

        self.assertEqual(len(SeededUpdate.objects.currently_available()), 0,
            "SeededUpdate should not be available after being sent")


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

    def test_all_seeded_updates_have_pub_dates_between_1_and_30_minutes(self):
        a = generate_random_authorized_account()
        generate_random_seeder(a)

        update = Update.objects.create(
            posted_by = a,
            original_text = "Hello from Seeder!"
        )

        seeded_update = SeededUpdate.objects.get(update = update)

        # only uses 59 seconds to avoid possible race condition where
        # more than a second elapses between creation and the time this
        # test runs
        begin_datetime = datetime.fromtimestamp(time.time() + 59)
        end_datetime = datetime.fromtimestamp(time.time() + (60 * 30) + 1)
        self.assertPubDateBetween(seeded_update, begin_datetime, end_datetime)

    def test_only_creates_new_seeded_updates_on_new(self):
        a = generate_random_authorized_account()
        generate_random_seeder(a)
        update = generate_random_update(a)

        self.assertEqual(len(SeededUpdate.objects.all()), 1,
            "Sanity check")

        update.save()
        self.assertEqual(len(SeededUpdate.objects.all()), 1,
            "Should only create SeededUpdates on save when new")

    def test_only_creates_for_non_expired_seeders(self):
        a = generate_random_authorized_account()
        s1 = generate_random_seeder(a)
        s2 = generate_random_seeder(a)

        s2.set_expires_on_in_days(-1)
        s2.save()

        update = generate_random_update(a)
        self.assertEquals(len(SeededUpdate.objects.all()), 1,
            "should only create one SeededUpdate since on has expired")



class TestOfAuthorizedAccount(TestCase):
    def test_default_account_returns_default_account(self):
        a = generate_random_authorized_account()
        a.twitter_id = settings.SEEDER['default_twitter_id']
        a.save()

        default_account = AuthorizedAccount.objects.default_account()
        self.assertEqual(settings.SEEDER['default_twitter_id'], default_account.twitter_id)

    def test_only_pulls_seeders_that_have_not_expired(self):
        a = generate_random_authorized_account()
        s = generate_random_seeder(a)

        self.assertEquals(len(a.seeder_set.currently_available()), 1,
            "sanity check: seeder_set.currently_available() should be one")

        s.expires_on = datetime.fromtimestamp(time.time() - 60)
        s.save()
        self.assertEquals(len(a.seeder_set.currently_available()), 0,
            "seeder_set.currently_available() should have no seeders")


class TestOfSeeder(TestCase):
    def test_automatically_expires_in_30_days(self):
        seeder = generate_random_seeder()
        expected_expires_on = datetime.fromtimestamp(time.time() + 60*60*24*30).date()
        self.assertEquals(seeder.expires_on.date(), expected_expires_on,
            "seeder.expires_on should default to 30 days")

    def test_can_set_by_expires_by_day(self):
        seeder = generate_random_seeder()
        seeder.set_expires_on_in_days(7)

        self.assertEquals(seeder.expires_on.date(), datetime.fromtimestamp(time.time() + 60*60*24*7).date(),
            "seeder.expires_on should be 7 days in the future")

    def test_can_take_a_string_as_parameter(self):
        seeder = generate_random_seeder()
        try:
            seeder.set_expires_on_in_days("7")
        except TypeError:
            self.fail("seeder.set_expires_on_in_days() unable to handle a string")

