import webbrowser

import tweepy as t

import flutterby_db as db
import flutterby_widgets as w

CONSUMER_KEY = 'Y9mmRBwdZVXeTsb97QTRg'
CONSUMER_SECRET = 'VOj3aY0kIZAQ65S7MM4g5Got3QfzQkn6r5q6jKsw'

def authenticate( account ):
    key, secret = db.get_account( account )
    auth = t.OAuthHandler( CONSUMER_KEY, CONSUMER_SECRET )
    if secret:
        auth.set_access_token( key, secret )
    else:
        try:
            redirect_url = auth.get_authorization_url()
            webbrowser.open( redirect_url )
        except tweepy.TweepError:
            print 'Error! Failed to get request token.'
            return None

        verifier = w.prompt_dialog( 'Please enter the PIN provided by Twitter.',
                                    'PIN' )

        try:
            auth.get_access_token( verifier )
        except tweepy.TweepError:
            print 'Error! Failed to get access token.'
            return None

        db.set_account( account, auth.access_token.key, auth.access_token.secret )

    return auth

def make_api( account, auth = None ):
    if not auth:
        auth = authenticate( account )
    return t.API( auth )

def get_public( account, auth = None ):
    api = make_api( account, auth )

    return api.public_timeline()

def get_friends( account, auth = None ):
    api = make_api( account, auth )

    return api.friends_timeline()

def get_save_friends( account, auth = None ):
    tweets = get_friends( account, auth )

    for tweet in tweets:
        if not db.tweet_exists( tweet_id = tweet.id ):
            db.add_tweet( account, tweet )
    return tweets
