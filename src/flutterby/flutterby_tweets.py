# -*- coding: utf-8 -*-
import os, re, threading, time, urllib, webbrowser

import gobject, pango
try:
    import pynotify
    NOTIFICATION = 'pynotify'
except:
    NOTIFICATION = None

import tweepy as t

from flutterby_functions import *

import flutterby_resources as res
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

        return auth

    return auth

def authenticate2( account, verifier, auth = None ):
    if not auth:
        auth = authenticate( account )
    try:
        auth.get_access_token( verifier )
    except t.TweepError:
        print 'Error! Failed to get access token.'
        return None
    db.set_account( account, auth.access_token.key, auth.access_token.secret )
    
    return auth

def make_api( account, auth = None ):
    if not auth:
        auth = authenticate( account )
    return t.API( auth )

### Timelines

def get_public( account, auth = None ):
    api = make_api( account, auth )

    return api.public_timeline()

def get_friends( account, auth = None ):
    api = make_api( account, auth )

    return api.friends_timeline()

def get_save_friends( account, auth = None ):
    tweets = get_friends( account, auth )

    for tweet in tweets:
        if not len( db.get_tweets( tweet_id = tweet.id,
                                   account = account ) ):
            db.add_tweet( account, tweet )
    return tweets

def get_home( account, auth = None ):
    api = make_api( account, auth )

    return api.home_timeline()

def get_save_home( account, auth = None ):
    tweets = get_home( account, auth )

    for tweet in tweets:
        if not len( db.get_tweets( tweet_id = tweet.id,
                                   account = account ) ):
            db.add_tweet( account, tweet )
    return tweets

### Followers/Following

def get_following_ids( account, auth = None ):
    api = make_api( account, auth )

    user = api.me()
    return api.friends_ids( user.id )

def get_following( account, auth = None ):
    return [ api.get_user( id ) for id in get_following_ids( account, auth ) ]

def get_follower_ids( account, auth = None ):
    api = make_api( account, auth )

    user = api.me()
    return api.followers_ids( user.id )

def get_followers( account, auth = None ):
    api = make_api( account, auth )
    return api.followers()

### Sending tweets

def tweet( account, text ):
    api = make_api( account )

    try:
        api.update_status( text )
        return True
    except t.TweepError:
        return False

### Authors

def author_image_filename( author ):
    url = author.profile_image_url
    filename = url.split( '/' )
    filename = '/'.join( [ filename[ -2 ],
                           filename[ -1 ] ] )
    filename = os.path.join( res.USER_IMAGE_PATH, filename )

    return url, filename

### Formatting tweets

def tweet_as_dict( tweet ):
    return { 'text' : tweet.text,
             'author' : '@' + tweet.author.screen_name,
             'full_name' : tweet.author.name,
             'double_name' : '%s (@%s)' % ( tweet.author.name,
                                            tweet.author.screen_name ),
             'username' : tweet.author.screen_name,
             'ago' : ago( time.mktime( tweet.created_at.timetuple() ) ),
             'client' : tweet.source,
             'client_url' : tweet.source_url,
             }

def tweet_as_text( tweet ):
    return ( 'From @%(author)s: %(text)s\nPosted %(ago)s via %(client)s\n\n' %
             tweet_as_dict( tweet ) )

def tweet_as_tag_list( tweet ):
    td = tweet_as_dict( tweet )
    
    ending_hashtag_re = re.compile( r'\s+(?P<hashtags>(#\w+\s*)+)\s*$' )
    hashtag_re = re.compile( r'#(?P<hashtag>\w+)\b' )
    replace_re = re.compile( r'#!#(?P<key>.*)#!#' )
    ref_re = re.compile( r'@(?P<username>\w+)\b' )
    response_re = re.compile( r'^\s*(?P<username>@\w+)\b' )
    retweet_re = re.compile( r'^\s*(?:RT|via)[:]?\s+' +
                             r'(?P<username>@\w+)\b( *[:-]+ *)?',
                             re.IGNORECASE ) 
    url_re = re.compile( unicode( r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', 'utf-8' ) )

    chosen_name = '#!#author#!#'
    if db.get_param( 'show_name', True ):
        chosen_name = '#!#double_name#!#'

    match = retweet_re.search( tweet.text )
    if match:
        ret = [ ('From ', 'start'),
                (match.group( 'username' ), 'username'),
                (' via ', None),
                (chosen_name, 'username'),
                (': ', None), ]
        tmp = [ (tweet.text[ match.end(): ], None) ]
    else:
        match = response_re.search( tweet.text )
        if match:
            ret = [ ('From ', 'start'),
                    (chosen_name, 'username'),
                    (' in response to ', None),
                    (match.group( 'username'), 'username'),
                    (': ', None), ]
            tmp = [ (tweet.text[ match.end(): ], None) ]
        else:
            ret = [ ('From ', 'start'),
                    (chosen_name, 'username'),
                    (': ', None), ]
            tmp = [ (tweet.text, None) ]
    text = tmp[0][0]
    match = ending_hashtag_re.search( text )
    if match:
        text = ''.join( [ text[:match.start()],
                          '  ',
                          match.group( 'hashtags' ) ] )
        tmp[0] = (text, None)
        
    def tag_blob( regex, use_tag ):
        tmp2 = []
        for text, tag in tmp:
            match = regex.search( text )
            while match:
                tmp2.append( (text[ :match.start() ], tag) )
                tmp2.append( (match.group( 0 ), use_tag) )

                text = text[ match.end(): ]
                match = regex.search( text )
            tmp2.append( (text, tag) )
        return tmp2

    tmp = tag_blob( url_re, 'url' )
    tmp = tag_blob( ref_re, 'username' )
    tmp = tag_blob( hashtag_re, 'hashtag' )

    tmp2 = []
    for text, tag in tmp:
        tmp2.append( (text, [tag, 'tweet']) )

    ret += tmp2

    if db.get_param( 'show_client' ):
        ret += [ ('\nPosted ', 'time'),
                 ('#!#ago#!#', 'time'),
                 (' via ', 'client' ),
                 ('#!#client#!#', 'client'),
                 ('.', 'client'), ]
    else:
        ret += [ ('\n', None),
                 ('Posted ', 'time'),
                 ('#!#ago#!#', 'time'),
                 ('.', 'time') ]

    for index in xrange( len( ret ) ):
        text, tag = ret[ index ]
        
        match = replace_re.match( text )
        if match:
            text = td[ match.group( 'key' ) ]

        if type( tag ) != list:
            tag = [ tag ]
        tag.append( custom_tag( 'from',
                                td[ 'username' ].lower() ) )

        ret[ index ] = (text, tag)
    
    return ret

class Timeline( list ):
    def __init__( self, account ):
        self.account = account

        super( Timeline, self ).__init__()

        self.db_load_timeline( limit = None )

    def __repr__( self ):
        return 'Timeline(%s)' % self.account

    def __str__( self ):
        return repr( self )

    def update( self, tweets ):
        ids = [ x.id for x in self ]
        tweets = [ tweet for tweet in tweets if tweet.id not in ids ]

        self += tweets

    def load_timeline( self, limit = 20, network = True ):
        if network:
            try:
                get_save_home( self.account )
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
    def __init__( self, timelines = [], view = None ):
        self.timelines = timelines
        
        self.new_buffer()
        self.listeners = []

    def __repr__( self ):
        return 'TimelineSet(%s)' % ', '.join( [ str( t ) for t in self.timelines ] )

    def __str__( self ):
        return repr( self )

    def make_buffer( self ):
        if hasattr( self, 'buffer' ) and self.buffer:
            buf = w.TweetTextBuffer( parent = self.buffer.parent )
        else:
            buf = w.TweetTextBuffer()

        return buf

    def new_buffer( self ):
        self.buffer = self.make_buffer()

    def add( self, timeline ):
        self.timelines.append( timeline )

    def add_list( self, li ):
        self.timelines += li
        self.refresh()

    def add_listener( self, listener ):
        if listener not in self.listeners:
            self.listeners.append( listener )

    def notify_listeners( self, message ):
        for l in self.listeners:
            l.notify( message )

    def tweets( self, limit = 20, network = True ):
        tweets = reduce( lambda x, y: x + y,
                         self.timelines,
                         [] )
        ids = [ x.id for x in tweets ]
        new_tweets = []
        for tl in self.timelines:
            tl.load_timeline( limit = limit,
                              network = network )
            new_tweets += [ x for x in tl if x.id not in ids ]

        if len( new_tweets ):
            print '\n'.join( [ tweet_as_text( tweet ) for tweet in new_tweets ] )

        tweets += new_tweets
        tweets.sort( key = lambda x: x.created_at,
                     reverse = True )

        if not db.get_param( 'show_retweets' ):
            tweets = [ tweet for tweet in tweets
                       if not hasattr( tweet, 'retweeted_status' ) ]
        
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

        for tweet in tweets:
            url, filename = author_image_filename( tweet.author )

            if os.path.exists( filename ):
                continue
            dirname = os.path.dirname( filename )
            if not os.path.exists( dirname ):
                os.mkdir( dirname )
                
            urllib.urlretrieve( url, filename )
            tweet.author.profile_image_file = filename

        if NOTIFICATION and db.get_param( 'new_tweet_notify', True ):
            for tweet in sorted( new_tweets,
                                 key = lambda x: x.created_at,
                                 reverse = False ):
                url, filename = author_image_filename( tweet.author )
                uri = None
                if os.path.exists( filename ):
                    uri = 'file://%s' % filename
                n = pynotify.Notification( tweet.author.screen_name,
                                           tweet.text,
                                           uri )
                n.show()
            
        return tweets

    def refresh( self, limit = 20, network = True ):
        print 'Refreshing'
        
        tweets = [ tweet_as_tag_list( tweet )
                   for tweet in self.tweets( limit = limit,
                                             network = network ) ]
        buf = self.make_buffer()
        count = 0
        point = buf.get_end_iter()
        for tweet in tweets:
            if count > 0:
                buf.insert_tag_list( point,
                                     [ ('\n\n', 'separator') ] )
            buf.insert_tag_list( point, tweet )
            count += 1        

        gobject.idle_add( self.update, buf )

    def update( self, new_buffer ):
        self.buffer = new_buffer

        self.notify_listeners( 'timeline buffer updated' )

class RefreshTimelines( threading.Thread ):
    def __init__( self, main_window, limit = 20, loop = True, permit_first = True ):
        self.main_window = main_window
        self.limit = limit
        self.loop = loop
        self.first_run = permit_first

        super( RefreshTimelines, self ).__init__()

        self.setDaemon( True )

    def start_spinner( self, account ):
        for key, tab in self.main_window.tab_items.items():
            if tab[ 'account' ] == account:
                tab[ 'entry' ].start_spinner()

    def stop_spinner( self, account ):
        for key, tab in self.main_window.tab_items.items():
            if tab[ 'account' ] == account:
                tab[ 'entry' ].stop_spinner()

    def run( self ):
        limit = self.limit
        if self.first_run:
            limit = None
        for timelines, account in [ ( v[ 'timelines' ], v[ 'account' ] )
                                    for v in self.main_window.tab_items.values() ]:
            gobject.idle_add( self.start_spinner, account )
            timelines.refresh( limit = limit )
            gobject.idle_add( self.stop_spinner, account )

        self.first_run = False
        delay = db.get_param( 'delay', 15 )
        if self.loop and delay > 0:
            delay *= 60.0
            time.sleep( delay )
            self.run()
