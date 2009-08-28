from django.conf import settings
from django.shortcuts import render_to_response, redirect
from oauthtwitter import OAuthApi
from seeder.models import AuthorizedAccount, Token, Seeder
from datetime import datetime
from urllib2 import HTTPError

def index(request):
    return render_to_response(
        'seeder/index.html'
    )

def _do_redirect(request):
    oauth = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'])
    request_token = oauth.getRequestToken()
    request.session['duration'] = request.POST['duration']
    request.session['twitter_request_token'] = request_token
    authorization_url = oauth.getAuthorizationURL(request_token)
    return redirect(authorization_url)

def signup(request, *args, **kwargs):
    if request.method == 'POST':
        return _do_redirect(request)

    return render_to_response('seeder/signup.html')

def finish(request):
    # TODO: refactor this out -- should be in a util class or on the model
    # TODO: add check for this, redirect if not found
    try:
        request_token = request.session['twitter_request_token']
        oauth = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'], request_token)
        access_token = oauth.getAccessToken()

        twitter = OAuthApi(settings.TWITTER['CONSUMER_KEY'], settings.TWITTER['CONSUMER_SECRET'], access_token)
        user_info = twitter.GetUserInfo()

        default_account = AuthorizedAccount.objects.default_account()

        s = Seeder(
            twitter_id = user_info.id,
            twitter_username = user_info.screen_name,
            authorized_for = default_account
        )
        s.set_expires_on_in_days(request.session['duration'])
        s.save()

        Token.objects.create(
            seeder = s,
            oauth_token = access_token.key,
            oauth_token_secret = access_token.secret
        )
    except HTTPError:
        pass

    return render_to_response('seeder/finish.html')

