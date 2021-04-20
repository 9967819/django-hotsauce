import base64
import hmac
import hashlib
import urllib
import unittest

def createhash(key, value):
    hash = hmac.new(key, value).hexdigest() 
    return base64.urlsafe_b64encode(hash)

def test_createhash():
    key = '1234'
    msg = '12'

    #base64 encoded data (the url)
    hash = createhash(key, msg)
    hash2 = hmac.new(key, base64.urlsafe_b64decode(hash)).hexdigest()
    
    assert hash == hash2, 'hmac keys not equal!'

if __name__ == '__main__':
    test_createhash()

