#!/usr/bin/python

import tweepy
import sys
import ConfigParser

#3208464

cfg = ConfigParser.ConfigParser()
cfg.read(sys.argv[1]+'/setup.conf')

section = 'keys'
auth = tweepy.OAuthHandler(cfg.get(section, 'consumer_key'), cfg.get(section, 'consumer_secret'))

print auth.get_authorization_url(signin_with_twitter=True)

pin = raw_input('PIN:')
auth.get_access_token(pin)
print 'token:', auth.access_token
print 'secret:', auth.access_token_secret


