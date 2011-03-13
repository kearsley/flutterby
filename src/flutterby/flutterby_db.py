import os, cPickle, time

import sqlite3 as s3

import flutterby_resources as res

def execute_multi( statements = [],
                   params = [],
                   pre_hook = None,
                   post_hook = None ):
    conn = s3.connect( res.USER_DATABASE )

    if pre_hook:
        pre_hook( conn, statement, params )

    c = conn.cursor()
    ret = []
    for statement, param in zip( statements, params ):
        if not param:
            param = ()
        c.execute( statement, param )
        ret.append( c.fetchall() )
    conn.commit()

    if post_hook:
        post_hook( conn, statement, params )

    c.close()

    return ret
        
def execute_sql( statement, params = None, pre_hook = None, post_hook = None ):
    return execute_multi( [ statement ], [ params ], pre_hook, post_hook )[0]

def build_db():
    if os.path.exists( res.USER_DATABASE ):
        return

    execute_sql( 'create table settings(key text unique, value text)' )
    execute_sql( 'create table accounts(name text unique, token text, secret text, last_checked integer)' )
    # execute_sql( 'create table following(id integer unique, screen_name text)' )
    execute_sql( 'create table tweets(id integer primary key asc, tweet_id integer unique, timestamp integer, account text, from_account text, tweet text)' )

def dump_table( name ):
    build_db()

    return execute_sql( 'select * from %s' % name )

def clear_table( name ):
    build_db()

    return execute_sql( 'delete from %s' % name )

def drop_table( name ):
    build_db()

    return execute_sql( 'drop table %s' % name )

### Parameters

def get_param( key, default = None ):
    build_db()
    
    params = execute_sql( 'select * from settings where key=?',
                          ( key, ) )

    if not len( params ):
        return default
    params = params[0]
    return cPickle.loads( str( params[1] ) )

def set_param( key, value ):
    build_db()

    value = cPickle.dumps( value )
    ret = execute_sql( 'insert or replace into settings (key, value) values(?, ?)',
                       ( key, value ) )

    return ret


### Accounts

def get_account( name ):
    build_db()

    ret = execute_sql( 'select token,secret from accounts where name=?',
                       ( name, ) )
    if not ret or not len( ret ):
        ret = (None, None)
    else:
        ret = ret[0]
    return ret

def set_account( name, token, secret ):
    build_db()

    ret = execute_sql( 'insert or replace into accounts (name, token, secret, last_checked) '
                       'values(?, ?, ?, ?)',
                       ( name, token, secret, 0 ) )

    return ret

def delete_account( name ):
    build_db()

    return execute_sql( 'delete from accounts where name=?',
                        ( name, ) )
    
def list_accounts():
    build_db()

    return [ x[0] for x in execute_sql( 'select name from accounts' ) ]

def accounts_exist():
    return len( list_accounts() ) > 0


### Tweets

def add_tweet( account, tweet ):
    from_account = unicode( tweet.author.screen_name )
    pickled_tweet = unicode( cPickle.dumps( tweet ).encode( 'base64' ) )
    timestamp = time.mktime( tweet.created_at.timetuple() )

    return execute_sql( 'insert or replace into tweets '
                        '(tweet_id, timestamp, account, from_account, tweet) '
                        'values(?, ?, ?, ?, ?)',
                        (tweet.id, timestamp, account, from_account, pickled_tweet) )

def tweet_where_clause( id = None,
                        account = None,
                        from_account = None,
                        tweet_id = None,
                        or_flag = False ):
    where = []
    values = []
    if id:
        where.append( 'id=?' )
        values.append( id )
    if account:
        where.append( 'account=?' )
        values.append( account )
    if from_account:
        where.append( 'from_account=?' )
        values.append( from_account )
    if tweet_id:
        where.append( 'tweet_id=?' )
        values.append( tweet_id )

    join_word = ' and '
    if or_flag:
        join_word = ' or '
    where_clause = ''
    if len( where ):
        where_clause = 'where %s' % ' and '.join( where )

    return where_clause, values

def get_tweets( id = None,
                account = None,
                from_account = None,
                tweet_id = None,
                or_flag = False ):
    where_clause, values = tweet_where_clause( id, account, from_account, tweet_id,
                                               or_flag )
    tweets = execute_sql( ( 'select * from tweets %s' %
                            where_clause ),
                          values )

    ret = []
    for x in tweets:
        try:
            ret.append( cPickle.loads( str( x[-1] ).decode( 'base64' ) ) )
        except:
            delete_tweets( id = x[0] )
    return ret

def delete_tweets( id = None,
                   account = None,
                   from_account = None,
                   tweet_id = None,
                   or_flag = False ):
    where_clause, values = tweet_where_clause( id, account, from_account, tweet_id,
                                               or_flag ) 
    tweets = execute_sql( 'delete from tweets %s' % where_clause,
                          values )
    return tweets

def tweet_exists( id = None, tweet_id = None ):
    tweets = get_tweets( id = id, tweet_id = tweet_id, or_flag = True )

    return len( tweets ) > 0
