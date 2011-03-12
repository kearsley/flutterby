import re, os, sys

from flutterby_functions import determine_path

BASE_PATH = determine_path()

RESOURCE_PATH = os.path.join( BASE_PATH, 'resources' )

IMAGE_PATH = os.path.join( RESOURCE_PATH, 'img' )
XML_PATH = os.path.join( RESOURCE_PATH, 'xml' )

def get_path( base_path, base_ext, filename ):
    name, ext = os.path.splitext( filename )
    if not ext:
        ext = base_ext

    filename = name + ext

    return os.path.join( base_path, filename )

def image_path( filename ):
    return get_path( IMAGE_PATH, '.png', filename )
