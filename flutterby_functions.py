import time

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
YEAR = 365 * DAY

def ago( timestamp ):
    now = time.mktime( time.gmtime() )
    delta = now - timestamp

    count, count2, word, word2 = None, None, None, None
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
        count2 = ( delta - count * HOUR ) // MINUTE
        word = 'hour'
        word2 = 'minute'
    elif delta > MINUTE:
        count = delta // MINUTE
        count2 = ( delta - count * MINUTE ) // SECOND
        word = 'minute'
        if count2:
            word2 = 'second'
        else:
            count2 = None
    else:
        count = delta // SECOND
        word = 'second'

    if not word or ( not count and count != 0 ):
        return ''
    if count != 1:
        word = pluralize( word )
    if word2 and count2:
        if count2 != 1:
            word2 = pluralize( word2 )
        return ( '%(c1)d %(w1)s and %(c2)d %(w2)s ago' %
                 { 'c1' : count,
                   'c2' : count2,
                   'w1' : word,
                   'w2' : word2,
                   } )
    return ( '%(c1)d %(w1)s ago' %
             { 'c1' : count,
               'c2' : count2,
               'w1' : word,
               'w2' : word2,
               } )
    
def pluralize( word ):
    return word + 's'
