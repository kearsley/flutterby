import os, cPickle

import sqlite3 as s3

DB_PATH = os.path.expanduser( '~/.flutterby_db' )

def execute_multi( statements = [],
                   params = [],
                   pre_hook = None,
                   post_hook = None ):
    conn = s3.connect( DB_PATH )

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
        
def execute_sql( statement, params = (), pre_hook = None, post_hook = None ):
    return execute_multi( [ statement ], [ params ], pre_hook, post_hook )[0]

def build_db():
    if os.path.exists( DB_PATH ):
        return

    execute_sql( 'create table settings(key text unique, value text)',
                 None )
    execute_sql( 'create table tweets(id integer primary key asc, '
                 'timestamp integer, '
                 'account text, '
                 'from_account text, '
                 'body text)',
                 None )

def dump_table( name ):
    build_db()

    return execute_sql( 'select * from %s' % name, None )

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
