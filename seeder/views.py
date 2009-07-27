from django.conf import settings
from django.shortcuts import render_to_response
from oauthtwitter import OAuthApi
#import oauthtwitter
#from oauth import oauth

#SERVER = getattr(settings, 'OAUTH_SERVER', 'twitter.com')
#ACCESS_TOKEN_URL = getattr(settings, 'OAUTH_ACCESS_TOKEN_URL', 'https://%s/twitter_app/access_token' % SERVER)
    
def index(request):
    return render_to_response(
        'seeder/index.html'
    )

def signup(request):
    oauth = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'])
    request_token = oauth.getRequestToken()
    request.session['twitter_request_token'] = request_token
    authorization_url = oauth.getAuthorizationURL(request_token)
    return render_to_response(
        'seeder/signup.html',
        {
            'authorization_url': authorization_url,
        }
    )

def finish(request):
    # TODO: refactor this out -- should be in a util class or on the model
    # TODO: add check for this, redirect if not found
    request_token = request.session['twitter_request_token']
    oauth = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'], request_token)
    access_token = oauth.getAccessToken()
    
    twitter = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'], access_token)
    user_info = twitter.GetUserInfo()

    default_account = AuthorizedAccount.objects.default_account()

    s = Seeder.objects.create(
        twitter_id = user_info.id,
        authorized_for = default_account
    )

    Token.objects.create(
        seeder = s,
        oauth_token = access_token.key,
        oauth_token_secret = access_token.secret
    )

    return render_to_response(
        'seeder/finish.html',
        {
            'user_info': user_info,
        }
    )

