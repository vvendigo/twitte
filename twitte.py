#!/usr/bin/python

#twitte-bot.com

import os, sys
import tweepy
import json
import tweetScorer
import random
import ConfigParser
import getopt
import glob
import time

print time.strftime('%Y-%m-%d %H:%M')

random.seed()

basePath = './'
dryRun = True

def usage():
    print 'Usage:', sys.argv[0], '[-h] [-t] [directory]'
    sys.exit()
#enddef

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht", ["help", "dryRun"])
except getopt.GetoptError as err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
#endtry

if len(args)>1:
    usage()
#endif
if len(args)>0:
    dryRun = False
    basePath = args[0]
#endif

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
    elif o in ("-t", "--dryRun"):
        dryRun = True
#endfor

if dryRun:
    print "DRY RUN!!! (set directory argument for real update)"

class LazyApiConnect:
    #primitive singleton giving API connection when needed

    def __init__(self, consumer_key, consumer_secret, access_key, access_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_key = access_key
        self.access_secret = access_secret
        self.api = None
    #enddef

    def getApi(self):
        if self.api == None:
            auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            auth.set_access_token(self.access_key, self.access_secret)
            self.api = tweepy.API(auth)
        #endif
        return self.api
    #enddef
#endclass


confs = glob.glob(os.path.join(basePath, '*', "setup.conf"))

# iterate directories/confs
for confPath in confs:
    # TODO: fork here?
    if dryRun:
        print confPath
    cfg = ConfigParser.ConfigParser()
    cfg.read(confPath)
    directory = os.path.dirname(confPath)
    accountId = os.path.split(directory)[1]
    section = 'keys'
    conn = LazyApiConnect(cfg.get(section, 'consumer_key'), cfg.get(section, 'consumer_secret'), \
                        cfg.get(section, 'access_key'), cfg.get(section, 'access_secret'))

    ownName = conn.getApi().auth.get_username()

    # random favorite
    section = 'favorite'
    if cfg.has_section(section) and cfg.getfloat(section, 'probability') > random.random():
        queries = []
        for q in cfg.get(section, 'query').split(','):
            q = q.strip()
            cnt = 20
            lang = 'en'
            p = q.rfind('[')
            if p>=0:
                cnt, lang = q[p+1:-1].split(' ')
                q = q[:p]
            query = {'query':q, 'count':int(cnt), 'lang':lang}
            if dryRun: print query
            queries.append(query)
        #endfor

        max_favorites = None
        if cfg.has_option(section, 'max_favorites'):
            max_favorites = cfg.getint(section, 'max_favorites')

        uniq = {}
        uniqUsers = {}
        # read favorites and set them to uniqs to prevent duplicity
        favCnt = 25
        if max_favorites: favCnt = max_favorites+5
        favTweets = conn.getApi().favorites(count=favCnt, include_entities=False)
        for tweet in favTweets:
            tweet.score = 666000
            uKey = tweetScorer.normalizeText(tweet)
            #print "'%s'"%uKey
            uniq[uKey] = tweet
            uniqUsers[tweet.user.screen_name] = tweet
        #endfor

        #print len(uniqUsers)

        tweets = []
        i = 0

        for query in queries:
            q = '%s since:%s'%(query['query'],time.strftime('%Y-%m-%d'))
            res = conn.getApi().search(q, count=query['count'], lang=query['lang'], result_type='recent')
            # since_id??
            for tweet in res:
                if tweet.retweeted or tweet.favorited or tweet.user.screen_name==ownName:
                    #print tweet.retweeted, tweet.favorited, tweet.user.screen_name
                    continue
                tweet.score = tweetScorer.getScore(tweet)
                uKey = tweetScorer.normalizeText(tweet)
                uUsr = tweet.user.screen_name
                #print "'%s'"%uKey
                if uniq.has_key(uKey):
                    if uniq[uKey].score < tweet.score:
                        uniq[uKey].score = -1
                        uniq[uKey] = tweet
                        if not uniqUsers.has_key(uUsr):
                            uniqUsers[uUsr] = tweet
                    else:
                        tweet.score = -666
                elif uniqUsers.has_key(uUsr):
                    if uniqUsers[uUsr].score < tweet.score:
                        uniqUsers[uUsr].score = -1
                        uniqUsers[uUsr] = tweet
                        uniq[uKey] = tweet
                    else:
                        tweet.score = -666
                else:
                    uniq[uKey] = tweet
                    uniqUsers[uUsr] = tweet

                tweets.append(tweet)
                i += 1
                #tweetScorer.printTweet(tweet)
                #print
            #endfor
        #endfor

        tweetScorer.sort(tweets)
        if dryRun: print 'Found', len(tweets)

        # favorite best
        i = 0
        errCnt = 0
        while len(tweets) > i and tweets[i].score > 0:
            print 'Favorite:', accountId, tweets[i].created_at, tweets[i].text.encode('utf-8', 'ignore')
            if dryRun:
                break
            try:
                tweets[i].favorite()
                break
            except:
                errCnt += 1
                if errCnt > 10:
                    raise
            i += 1
        #endwhile

        # trim favorites list
        if dryRun: print max_favorites, len(favTweets)
        if max_favorites:
            for tweet in favTweets[max_favorites:]:
                print 'Unfavorite:', accountId, tweet.created_at, tweet.text.encode('utf-8', 'ignore')
                if dryRun:
                    continue
                conn.getApi().destroy_favorite(tweet.id)
                #print tweet._json
            #endfor
        #endif
    #endif

    # tweeting
    section = 'tweet'
    if cfg.has_section(section):
        # timed
        timedTweetSent = False
        tweetFiles = glob.glob(os.path.join(directory, time.strftime('%Y-%m-%d-*.tweet')))
        tweetFiles.sort()
        for tf in tweetFiles:
            #print tf
            t = tf[-10:-6]
            #print t, time.strftime('%H%M')
            if t <= time.strftime('%H%M'):
                msg = file(tf).read().decode('utf-8').strip()
                print 'Timed tweet:', accountId, tf, msg.encode('utf-8', 'ignore')
                if dryRun:
                    pass
                else:
                    conn.getApi().update_status(msg)
                    os.remove(tf)
                timedTweetSent = True
            #endif
        #endfor
        # random
        if not timedTweetSent and cfg.getfloat(section, 'probability') > random.random():
            tweetFiles = glob.glob(os.path.join(directory, 'random*.tweet'))
            if len(tweetFiles):
                tf = random.choice(tweetFiles)
                msg = file(tf).read().decode('utf-8').strip()
                print 'Random tweet:', accountId, tf , msg.encode('utf-8', 'ignore')
                if dryRun:
                    pass
                else:
                    conn.getApi().update_status(msg)
                    os.remove(tf)
            #endif
        #endif
    #endif

#endfor
