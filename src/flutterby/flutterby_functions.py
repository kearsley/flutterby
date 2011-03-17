import inspect, os, sys, time

DEBUG_MESSAGES = 8
DEBUG_EVENTS = 16
DEBUG = reduce( lambda x, y: x | y,
                [ DEBUG_MESSAGES,
                  DEBUG_EVENTS,
                  ],
                0 )

def dprint( level, message, **args ):
    if DEBUG & level:
        print message.format( args )

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
YEAR = 365 * DAY

def ago( timestamp ):
    now = time.mktime( time.gmtime() )
    delta = now - timestamp

    if delta > YEAR:
        count = delta // YEAR
        word = 'year'
    elif delta > WEEK:
        count = delta // WEEK
        word = 'week'
    elif delta > DAY:
        count = delta // DAY
        word = 'day'
    elif delta > HOUR:
        count = delta // HOUR
        word = 'hour'
    elif delta > MINUTE:
        count = delta // MINUTE
        word = 'minute'
    else:
        count = delta // SECOND
        word = 'second'

    if not word or ( not count and count != 0 ):
        return ''
    if delta < 30 * SECOND:
        return 'just now'
    if count != 1:
        word = pluralize( word )
    return ( '%(c1)d %(w1)s ago' %
             { 'c1' : count,
               'w1' : word } )
    
def pluralize( word ):
    return word + 's'

def determine_path():
    root = inspect.getfile( inspect.currentframe() )
    
    if os.path.islink( root ):
        root = os.path.realpath( root )
    return os.path.dirname( os.path.abspath( root ) )


### Tags

CUSTOM_TAG = '@ct@'

def is_custom_tag( tag ):
    split_tag = custom_tag_split( tag )[0]

    if split_tag == CUSTOM_TAG:
        return True
    return False

def custom_tag( tag, payload = None ):
    tag = [ CUSTOM_TAG, tag ]
    if payload:
        tag.append( payload )

    return ':'.join( tag )

def custom_tag_split( tag ):
    return tag.split( ':' )

def custom_tag_name( tag ):
    return custom_tag_split( tag )[1]

def custom_tag_payload( tag ):
    split_tag = custom_tag_split( tag )

    if len( split_tag ) >= 3:
        return split_tag[2]
    return None
