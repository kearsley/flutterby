import webbrowser

import twitter as t

import flutterby_db as db
import flutterby_widgets as widgets

CONSUMER_KEY = 'j7Fp4cAHlZe3TPoVkoTkeg'
CONSUMER_SECRET = 'RFpGkyNE8zqTIbYcysWIw7oNPKqriSHYZwNj5Frzrf4'

def authenticate( account ):
    oauth_token, oauth_token_secret = db.get_account( account )

    if not oauth_token or not oauth_token_secret:
        auth = t.OAuth( '', '', CONSUMER_KEY, CONSUMER_SECRET )
        twitter = t.Twitter( auth = auth,
                             format = '' )
        ( oauth_token,
          oauth_token_secret ) = parse_oauth_tokens( twitter.oauth.request_token() )

        oauth_url = ( 'http://api.twitter.com/oauth/authorize?oauth_token=%s' %
                      oauth_token )
        try:
            r = webbrowser.open( oauth_url )
            if not r:
                raise Exception()
        except:
            return None

        oauth_verifier = widgets.prompt_dialog( 'Please enter the PIN given '
                                                'by Twitter.',
                                                'PIN' )
        oauth_verifier = oauth_verifier.strip()

        auth = t.OAuth( oauth_token,
                        oauth_token_secret,
                        CONSUMER_KEY,
                        CONSUMER_SECRET )
        twitter = t.Twitter( auth = auth,
                             format='' )
        ( oauth_token, oauth_token_secret ) = parse_oauth_tokens( twitter.oauth.access_token( oauth_verifier=oauth_verifier ) )

        db.set_account( account, oauth_token, oauth_token_secret )

    twitter = t.Twitter( auth = t.OAuth( oauth_token,
                                         oauth_token_secret,
                                         CONSUMER_KEY,
                                         CONSUMER_SECRET ),
                         format = '' )
    return twitter

def parse_oauth_tokens(result):
    for r in result.split('&'):
        k, v = r.split('=')
        if k == 'oauth_token':
            oauth_token = v
        elif k == 'oauth_token_secret':
            oauth_token_secret = v
    return oauth_token, oauth_token_secret
