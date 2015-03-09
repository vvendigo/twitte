import re

#weights = {'#cnt': -0.12288000000000002, 'favourites_ratio': 1.6588799999999997, 'RT ': -2.0736, 'hashtags': -0.06144000000000001, '?cnt': -0.9216, 'followers_count': 0.0020735999999999997, 'friends_ratio': 0.6144000000000002, 'user_mentions': -0.30720000000000003, 'length': 0.04608000000000001, 'in_reply_to_screen_name': -0.9216000000000001, 'urls': 2.0736000000000003, '!cnt': 0.06144000000000002, 'retweet_count': 0.24576000000000003, 'favorite_count': 0.4608, 'in_reply_to_status': -1.152}
#weights = {'#cnt': -0.09830400000000002, 'favourites_ratio': 1.3271039999999998, 'RT ': -2.48832, 'hashtags': -0.04915200000000001, '?cnt': -0.73728, 'followers_count': 0.0016588799999999997, 'friends_ratio': 0.4915200000000002, 'user_mentions': -0.24576000000000003, 'length': 0.05529600000000001, 'in_reply_to_screen_name': -0.7372800000000002, 'urls': 1.6588800000000004, '!cnt': 0.04915200000000002, 'retweet_count': 0.294912, 'favorite_count': 0.36864, 'in_reply_to_status': -1.152}
#weights = {'#cnt': -0.14745600000000003, 'favourites_ratio': 0.6635519999999999, 'RT ': -1.24416, 'hashtags': -0.024576000000000004, '?cnt': -1.10592, 'followers_count': 0.0008294399999999999, 'friends_ratio': 0.2457600000000001, 'user_mentions': -0.12288000000000002, 'length': 0.027648000000000006, 'in_reply_to_screen_name': -1.1059200000000002, 'urls': 2.4883200000000008, '!cnt': 0.04915200000000002, 'retweet_count': 0.294912, 'favorite_count': 0.18432, 'in_reply_to_status': -1.152}
#weights = {'.cnt':1.0,'favourites_ratio': 0.6635519999999999, 'RT ': -1.24416, 'hashtags': -1.0, '?cnt': -1.0, 'followers_count': 0.1, 'friends_ratio': 0.2457600000000001, 'user_mentions': -1.0, 'length': 1.0, 'in_reply_to_screen_name': -1.1059200000000002, 'urls': 4.0, '!cnt': 1.0, 'retweet_count': 1.0, 'favorite_count': 1.0, 'in_reply_to_status': -1.152}
weights = {'favourites_ratio': 0.9953279999999999, 'RT ': -1.86624, 'hashtags': -0.5, '?cnt': -0.5, 'followers_count': 0.05, 'friends_ratio': 0.36864000000000013, '.cnt': 0.5, 'user_mentions': -0.5, 'length': 0.5, 'in_reply_to_screen_name': -0.5529600000000001, 'urls': 2.0, '!cnt': 1.0, 'retweet_count': 1.0, 'favorite_count': 0.5, 'in_reply_to_status': -1.152}

def getScore(tweet):
    global weights
    score = 0
    # shares
    score += weights['retweet_count'] * min(tweet.retweet_count, 10)/10.0
    score += weights['favorite_count'] * min(tweet.favorite_count, 10)/10.0
    # entities
    score += weights['user_mentions'] * min(len(tweet.entities['user_mentions']), 3)/3.0
    score += weights['urls'] * min(len(tweet.entities['urls']), 3)/3.0
    score += weights['hashtags'] * min(len(tweet.entities['hashtags']), 6)/6.0
    # tweet author score
    score += weights['followers_count'] * min(tweet.user.followers_count,1000)/1000.0
    if tweet.user.friends_count>0 and tweet.user.followers_count>0:
        score += weights['friends_ratio'] * tweet.user.friends_count/float(tweet.user.followers_count)
    if tweet.user.statuses_count:
        score += weights['favourites_ratio'] * tweet.user.favourites_count/float(tweet.user.statuses_count)
    # text analysis
    score += weights['length'] * len(tweet.text)/140.0
    if tweet.text.startswith('RT '):
        score += weights['RT '] * 5
    score += -0.25 + weights['?cnt'] * min(tweet.text.count('?'),4)/4.0
    score += -0.25 + weights['!cnt'] * min(tweet.text.count('!'),4)/4.0
    score += -0.5 + weights['.cnt'] * min(tweet.text.count('.'),4)/4.0
    # reply
    if tweet.in_reply_to_status_id:
        score += weights['in_reply_to_status'] * 10
    if tweet.in_reply_to_screen_name:
        score += weights['in_reply_to_screen_name'] * 10

    return score
#enddef


def printTweet(tweet):
    print '#',
    for k in ('score', 'text','in_reply_to_status_id', 'in_reply_to_screen_name', "created_at"):
        print ("%s=%s"%(k.encode('utf-8','ignore'), tweet.__dict__[k])).replace('\n',' ').encode('utf-8', 'ignore'),
    #endfor
    print
    user = tweet.user
    print '#',
    for k in ('screen_name','friends_count','followers_count',"listed_count","statuses_count","favourites_count"):
        print ("%s=%s"%(k.encode('utf-8','ignore'), tweet.user.__dict__[k])),
    print
#enddef

re_norm  = re.compile('@\S*|https?://\S*|#\w*')
re_norm2 = re.compile('"+|\'+|\.|\!|\?|\s+')

def normalizeText(tweet):
    global re_norm
    clean = re_norm.sub('',tweet.text)
    clean = re_norm2.sub(' ',clean)
    clean = [w for w in clean.split(' ') if len(w)>2]
    return ' '.join(sorted(set(clean))[:13])
#enddef

def sort(tweets):
	tweets.sort(lambda a,b: cmp(a.score,b.score), reverse=True)
#enddef


