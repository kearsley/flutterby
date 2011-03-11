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

class Timeline( set ):
    def __init__( self, account ):
        self.account = account

        super( Timeline, self ).__init__()

    def tweet_list( self, limit = 20 ):
        try:
            get_save_friends( self.account )
        except t.TweepError, e:
            print e
    
        tweets = db.get_tweets( account = self.account )
        if limit and len( tweets ) > limit:
            tweets = tweets[:( limit - 1 )]
        self.update( tweets )

        return tweets
    
class TimelineSet:
    def __init__( self, timelines = [] ):
        self.timelines = timelines
        
        self.buffer = w.TextBuffer()

    def add( self, timeline ):
        self.timelines.add( timeline )
        self.refresh()

    def add_list( self, li ):
        self.timelines += li
        self.refresh()

    def refresh( self, limit = 20 ): 
        tweets = []
        for tl in self.timelines:
            filtered = [ x for x in tl.tweet_list( limit = limit )
                         if x.id not in [ y.id for y in tweets ] ]
            print [ x.text for x in filtered ]
            tweets += filtered
        tweets.sort( key = lambda x: x.created_at,
                     reverse = True )
        start, end = self.buffer.get_bounds()
        self.buffer.delete( start, end )
        start, point = self.buffer.get_bounds()
        for tweet in tweets:
            self.buffer.insert( point,
                                tweet_as_text( tweet ) )

class RefreshTimelines( threading.Thread ):
    def __init__( self, main_window, limit = 20, loop = True ):
        self.main_window = main_window
        self.limit = limit
        self.loop = loop

        super( RefreshTimelines, self ).__init__()

    def start_spinner( self ):
        self.main_window.entry.start_spinner()

    def stop_spinner( self ):
        self.main_window.entry.stop_spinner()

    def run( self ):
        gobject.idle_add( self.start_spinner )
        self.main_window.timelines.refresh( limit = self.limit )
        gobject.idle_add( self.stop_spinner )

        if self.loop:
            threading.Timer( db.get_param( 'delay', 15 ) * 60.0,
                             self.run )
