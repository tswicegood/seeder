from django.conf import settings
from oauth import oauth
from oauthtwitter import OAuthApi

# TODO: allow injection of OAuthApi
# TODO: allow injection of settings
class TwitterPoster(object):
    def _generate_access_token_from_model(self, model):
        return oauth.OAuthToken(model.oauth_token, model.oauth_token_secret)

    def post(self, update):
        tokens = update.seeder.token_set.all()
        # TODO: would look so much prettier as a list comprehension
        for token in tokens:
            twitter = OAuthApi(
                settings.TWITTER['CONSUMER_KEY'],
                settings.TWITTER['CONSUMER_SECRET'],
                self._generate_access_token_from_model(token)
            )

            source = "seeder"
            if settings.TWITTER.has_key("SOURCE"):
                source = settings.TWITTER['SOURCE']

            twitter.SetSource(source)
            twitter.PostUpdate(update.update.original_text)

