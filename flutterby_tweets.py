import threading, time, webbrowser

import gobject

import tweepy as t

import flutterby_db as db
import flutterby_widgets as w

from flutterby_functions import *

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


### Sending tweets

def tweet( account, text ):
    api = make_api( account )

    try:
        api.update_status( text )
        return True
    except t.TweepError:
        return None

### Formatting tweets

def tweet_as_dict( tweet ):
    return { 'text' : tweet.text,
             'author' : tweet.author.screen_name,
             'ago' : ago( time.mktime( tweet.created_at.timetuple() ) ),
             'client' : tweet.source,
             'client_url' : tweet.source_url,
             }

def tweet_as_text( tweet ):
    return ( 'From @%(author)s: %(text)s\nPosted %(ago)s via %(client)s\n\n' %
             tweet_as_dict( tweet ) )

class Timeline( list ):
    def __init__( self, account ):
        self.account = account

        super( Timeline, self ).__init__()

        self.db_load_timeline( limit = None )

    def update( self, tweets ):
        ids = [ x.id for x in self ]
        tweets = [ tweet for tweet in tweets if tweet.id not in ids ]

        self += tweets

    def load_timeline( self, limit = 20 ):
        try:
            get_save_friends( self.account )
        except t.TweepError, e:
            print e

        self.db_load_timeline( limit )

    def db_load_timeline( self, limit = 20 ):
        tweets = db.get_tweets( account = self.account )
        tweets.sort( key = lambda x: x.created_at,
                     reverse = True )
        
        if limit and len( tweets ) > limit:
            tweets = tweets[:( limit - 1 )]
        self.update( tweets )

    def sorted_tweets( self ):
        tweets = list( self )
        tweets.sort( key = lambda x: x.created_at,
                     reverse = True )
        
        return tweets
    
class TimelineSet:
    def __init__( self, timelines = [] ):
        self.timelines = timelines
        
        self.buffer = w.TextBuffer()

    def add( self, timeline ):
        self.timelines.append( timeline )
        self.refresh()

    def add_list( self, li ):
        self.timelines += li
        self.refresh()

    def tweets( self, limit = 20 ):
        tweets = []
        for tl in self.timelines:
            tl.load_timeline( limit = limit )
            ids = [ x.id for x in tweets ]
            tweets += [ x for x in tl if x.id not in ids ]
        tweets.sort( key = lambda x: x.created_at,
                     reverse = True )

        tweet_count = db.get_param( 'tweet_count' )
        if tweet_count > 0 and len( tweets ) > tweet_count:
            tweets = tweets[:( tweet_count - 1 )]

        tweet_age = db.get_param( 'tweet_age' )
        if tweet_age > 0:
            tweet_age *= 3600
            tweets = [ tweet for tweet in tweets
                       if ( ( time.mktime( time.gmtime() ) -
                              time.mktime( tweet.created_at.timetuple() ) ) <
                            tweet_age ) ]
        
        return tweets

    def refresh( self, limit = 20 ):
        buf = w.TextBuffer()
        point = buf.get_end_iter()
        for tweet in self.tweets():
            buf.insert( point, tweet_as_text( tweet ) )

        gobject.idle_add( self.update, buf )

    def update( self, new_buffer ):
        start, end = new_buffer.get_bounds()
        self.buffer.set_text( new_buffer.get_text( start, end ) )
        
        return self.buffer

class RefreshTimelines( threading.Thread ):
    def __init__( self, main_window, limit = 20, loop = True, permit_first = True ):
        self.main_window = main_window
        self.limit = limit
        self.loop = loop
        self.first_run = permit_first

        super( RefreshTimelines, self ).__init__()

    def start_spinner( self ):
        self.main_window.entry.start_spinner()

    def stop_spinner( self ):
        self.main_window.entry.stop_spinner()

    def run( self ):
        gobject.idle_add( self.start_spinner )
        limit = self.limit
        if self.first_run:
            limit = None
        self.main_window.timelines.refresh( limit = limit )
        gobject.idle_add( self.stop_spinner )

        self.first_run = False
        if self.loop and db.get_param( 'delay' ) > 0:
            threading.Timer( db.get_param( 'delay', 15 ) * 60.0,
                             self.run )
