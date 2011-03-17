import re, os, sys

import gtk

from flutterby_functions import determine_path

BASE_PATH = determine_path()

RESOURCE_PATH = os.path.join( BASE_PATH, 'resources' )

IMAGE_PATH = os.path.join( RESOURCE_PATH, 'img' )
XML_PATH = os.path.join( RESOURCE_PATH, 'xml' )

USER_PATH = os.path.expanduser( '~/.flutterby' )

USER_IMAGE_PATH = os.path.join( USER_PATH, 'img' )

USER_DATABASE = os.path.join( USER_PATH, 'flutterby.sqlite3' )

def get_path( base_path, base_ext, filename ):
    name, ext = os.path.splitext( filename )
    if not ext:
        ext = base_ext

    filename = name + ext

    return os.path.join( base_path, filename )

IMAGES = {}
PIXBUFS = {}

def image_path( filename ):
    return get_path( IMAGE_PATH, '.png', filename )

def get_image( filename, tweet = None ):
    id = None
    if tweet:
        id = '%s:%s' % ( tweet.account, unicode( tweet.id ) )
    
    if id and IMAGES.has_key( id ):
        return IMAGES[ id ]

    if os.path.isabs( filename ):
        path = filename
    else:
        path = image_path( filename )

    pixbuf = None
    if PIXBUFS.has_key( path ):
        pixbuf = PIXBUFS[ path ]

    if not pixbuf and not os.path.exists( path ):
        return None

    if not pixbuf:
        pixbuf = gtk.gdk.pixbuf_new_from_file( path )
        PIXBUFS[ path ] = pixbuf
    
    img = gtk.image_new_from_pixbuf( pixbuf )
    if id:
        IMAGES[ id ] = img

    return img

def setup_user_paths():
    for path in [ USER_PATH, USER_IMAGE_PATH ]:
        if not os.path.exists( path ):
            os.mkdir( path )
    
