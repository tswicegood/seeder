from django import conf
from oauth import oauth
import oauthtwitter

class TwitterPoster(object):
    def __init__(self, api_class = oauthtwitter.OAuthApi, settings = conf.settings):
        self.api_class = api_class
        self.settings = settings

    def _generate_access_token_from_model(self, model):
        return oauth.OAuthToken(model.oauth_token, model.oauth_token_secret)

    def post(self, update):
        tokens = update.seeder.token_set.all()
        # TODO: would look so much prettier as a list comprehension
        for token in tokens:
            twitter = self.api_class(
                self.settings.TWITTER['CONSUMER_KEY'],
                self.settings.TWITTER['CONSUMER_SECRET'],
                self._generate_access_token_from_model(token)
            )

            source = "seeder"
            if self.settings.TWITTER.has_key("SOURCE"):
                source = self.settings.TWITTER['SOURCE']
            twitter.SetSource(source)

            template = "%s"
            if self.settings.TWITTER.has_key("POST_TEMPLATE"):
                template = self.settings.TWITTER['POST_TEMPLATE']
            twitter.PostUpdate(template % update.update.original_text)

