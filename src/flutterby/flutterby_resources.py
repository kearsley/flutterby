import re, os, sys

import gtk

from flutterby_functions import determine_path
from flutterby_widgets import UserIcon

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

def get_pixbuf( filename ):
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

    return pixbuf

def get_image_of_class( filename, class_type, id = None ):
    if id and IMAGES.has_key( id ):
        return IMAGES[ id ]

    pixbuf = get_pixbuf( filename )
    if not pixbuf:
        return None
    
    img = class_type()
    img.set_from_pixbuf( pixbuf )
    if id:
        IMAGES[ id ] = img

    return img

def get_image( filename ):
    return get_image_of_class( filename, gtk.Image )    

def get_usericon( filename, tweet = None ):
    id = None
    if tweet:
        id = '%s:%s' % ( tweet.account, unicode( tweet.id ) )
    
    return get_image_of_class( filename, UserIcon, id )

def setup_user_paths():
    for path in [ USER_PATH, USER_IMAGE_PATH ]:
        if not os.path.exists( path ):
            os.mkdir( path )
    
