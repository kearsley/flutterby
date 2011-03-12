import os, sys, time

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
    root = __file__
    if os.path.islink (root):
        root = os.path.realpath (root)
    return os.path.dirname (os.path.abspath (root))
