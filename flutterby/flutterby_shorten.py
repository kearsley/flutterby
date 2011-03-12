from re import match
from urllib2 import urlopen, Request, HTTPError
from urllib import quote
from simplejson import loads

class ShortenError( Exception ):
    pass

def shorten( url, service = 'goo.gl' ):
    if not service:
        return url
    service = service.lower()

    service_api = SERVICES[ service ]

    if type( service_api ) == type( shorten ):
        return service_api( url )

def goo_gl( url ):
    if not match('http://',url):
        raise ShortenError('URL must start with "http://"')
    try:
        response = urlopen( Request( 'http://goo.gl/api/url',
                                     'url=%s' % quote( url ),
                                     { 'User-Agent' : 'toolbar' } ) )
        data = response.read()
        data = loads( data )

        return data[ 'short_url' ]
    except HTTPError, e:
        j = loads( e.read() )
        if 'short_url' not in j:
            try:
                from pprint import pformat
                j = pformat(j)
            except ImportError:
                j = j.__dict__
                raise ShortenError( "Didn't get a correct-looking response. "
                                 "How's it look to you?\n\n%s" % j)
        return j['short_url']
    raise ShortenError('Unknown eror forming short URL.')

SERVICES = {
    'goo.gl' : goo_gl,
    }

