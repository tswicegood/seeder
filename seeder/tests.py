from django.test import TestCase as DjangoTestCase
from django.conf import settings
from seeder.models import *
from seeder.posters import TwitterPoster
from random import randint as random
from datetime import datetime
import time
import mox
import re

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

def generate_random_token(seeder = None):
    if seeder is None:
        seeder = generate_random_seeder()
    return Token.objects.create(
        seeder = seeder,
        oauth_token = "some token" + str(random(10, 100)),
        oauth_token_secret = "some token secret" + str(random(10, 100))
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


def generate_mock_settings():
    return mox.MockObject(settings)

class StubTwitterApi(object):
    number_of_calls = 0
    calls = []
    def __init__(self, *args, **kwargs):
        StubTwitterApi.number_of_calls += 1

    def __getattribute__(self, method):
        StubTwitterApi.calls.append(method)
        return self

    def __call__(self, *args, **kwargs):
        last_call = StubTwitterApi.calls.pop()
        StubTwitterApi.calls.append({
            "name": last_call,
            "args": args,
            "kwargs": kwargs,
        })


class SanityTestOfStubTwitterApi(TestCase):
    def setUp(self):
        super(SanityTestOfStubTwitterApi, self).setUp()
        StubTwitterApi.number_of_calls = 0

    def test_sanity_check(self):
        obj1 = StubTwitterApi()
        self.assertEqual(StubTwitterApi.number_of_calls, 1)
        obj2 = StubTwitterApi()
        self.assertEqual(StubTwitterApi.number_of_calls, 2)
        obj3 = StubTwitterApi()
        self.assertEqual(StubTwitterApi.number_of_calls, 3)

    def test_keeps_track_of_calls(self):
        obj = StubTwitterApi()
        obj.foobar()
        self.assertEqual(len(StubTwitterApi.calls), 1)

    def test_keeps_track_of_parameters_passed_in_to_methods(self):
        obj = StubTwitterApi()
        number = random(10, 100)
        obj.foobar(number)

        data = StubTwitterApi.calls.pop()
        self.assertEquals(data['args'], (number,))

def generate_full_update(number_of_seeders):
    account = generate_random_authorized_account()
    [generate_random_token(generate_random_seeder(account)) for i in range(number_of_seeders)]
    update = generate_random_update(account)
    return update

class StubSettingsForTwitterApi(object):
    TWITTER = {
        "CONSUMER_KEY": "foobar",
        "CONSUMER_SECRET": "barfoo",
    }


class TestOfTwitterPoster(TestCase):
    def setUp(self):
        super(TestOfTwitterPoster, self).setUp()
        StubTwitterApi.number_of_calls = 0
        StubTwitterApi.calls = []

    def test_encapsulates_post_in_template_string(self):
        settings = StubSettingsForTwitterApi()
        random_prefix = "random %d" % random(10, 100)
        settings.TWITTER["POST_TEMPLATE"] = "%s: %%s" % random_prefix

        u = generate_full_update(1)
        poster = TwitterPoster(api_class = StubTwitterApi, settings = settings)
        poster.post(u.seededupdate_set.all()[0])

        for data in StubTwitterApi.calls:
            if data['name'] == 'PostUpdate':
                break
        (posted_status,) = data['args']
        expected_status = "%s: .*" % random_prefix
        self.assertTrue(
            re.compile(expected_status).match(posted_status) is not None
        )


    def test_instantiates_new_api_class_for_each_token(self):
        number_of_seeders = random(2, 10)
        u = generate_full_update(number_of_seeders)
        
        poster = TwitterPoster(api_class = StubTwitterApi)
        [seeded_update.send(poster) for seeded_update in u.seededupdate_set.all()]

        self.assertEquals(StubTwitterApi.number_of_calls, number_of_seeders)

    def assertSetSourceCalledWith(self, value):
        for data in StubTwitterApi.calls:
            if data["name"] == "SetSource":
                break
        self.assertEquals((value,), data["args"])


    def test_sets_source_to_seeder_if_not_configured(self):
        u = generate_full_update(1)
        poster = TwitterPoster(api_class = StubTwitterApi)
        poster.post(u.seededupdate_set.all()[0])

        self.assertSetSourceCalledWith("seeder")

    def test_sets_source_to_configured_value(self):
        settings = StubSettingsForTwitterApi()
        random_source = "random value: " + str(random(10, 100))
        settings.TWITTER["SOURCE"] = random_source

        u = generate_full_update(1)
        poster = TwitterPoster(api_class = StubTwitterApi, settings = settings)
        poster.post(u.seededupdate_set.all()[0])

        self.assertSetSourceCalledWith(random_source)

