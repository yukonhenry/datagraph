# -*- coding: utf-8 -*-
# above needed to support regex pattern below
# refer to 'Mining Social Web' for installing sixohsix twitter api python package
# upgrade using 'sudo pip install twitter --upgrade'

import twitter
from nltk import FreqDist, regexp_tokenize, clean_html
from nltk.corpus import stopwords
import json
from collections import namedtuple
from urllib2 import urlopen, Request, URLError
import requests
# ref http://docs.python.org/2/howto/urllib2.html
# for handling or urlopen errors
#import twitter_text  no need to use this, use twitter api

# reference "Mining the Social Web"
def getTweets(name):
    ts = twitter.Twitter(domain="search.twitter.com")
    search_results = []
    for page in range(1,6):
        search_results.append(ts.search(q=name ,count=100, page=page, lang='en', include_entities=True))
    #search_results.append(ts.search(q=name ,count=100, lang='en', include_entities=True))
    #print json.dumps(search_results, sort_keys=True, indent=1)
    # refer to https://dev.twitter.com/docs/tweet-entities
    # for info on entities
    tweets = [ r['text'] for result in search_results for r in result['results']]
    #print tweets
    #raw_input()
    return tweets

def getTweetUrls(name):
    ts = twitter.Twitter(domain="search.twitter.com")
    search_results = []
    for page in range(1,6):
        search_results.append(ts.search(q=name+" filter:links",
                                        count=100, page=page, lang='en', include_entities=True))
    #print search_results
    #print json.dumps(search_results, sort_keys=True, indent=1)
    # refer to https://dev.twitter.com/docs/tweet-entities
    # for info on entities
    tweet_urls = [s['expanded_url'] for result in search_results for r in result['results'] \
                   for s in r['entities']['urls']]
    #print tweets
    #raw_input()
    return tweet_urls

def getwords(tweets):
    pattern = r'''(?xi)
       ([A-Z]\.)+
       | (RT|via)((?:\b\W*@\w+)+)
       | ((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|(([^\s()<>]+|(([^\s()<>]+)))*))+(?:(([^\s()<>]+|(([‌​^\s()<>]+)))*)|[^\s`!()[]{};:'".,<>?«»“”‘’]))
       | \w+([-':.]\w+)*
       | \$?\d+(\.\d+)?%?
       | \.\.\.\
       | @\w+
       # | [][.,;"'?():-_`]  # ignore single punctuation characters
       '''
    words = []
    for t in tweets:
#        words += [w.lower() for w in t.split()]
        tokens = regexp_tokenize(t, pattern)
        words += [w.lower() for w in tokens]
#    print "length="+str(len(words))
    return words

def filterdist_words(words):
    sw = stopwords.words('english')
    swu = [unicode(sw) for sw in sw]
    uwords = dropList(words, swu)
    #uwords = [w for w in words if w not in swu]
    freq_dist = FreqDist(uwords)
#    for p in freq_dist.items()[:150]:
#        print p[0],p[1]
    return freq_dist

# use python filter command to drop sublist from list
# http://www.codercaste.com/2010/01/11/how-to-filter-lists-in-python/
# from http://isites.harvard.edu/fs/docs/icb.topic211038.files/FedPapExamp_edited.py
def dropList(mylist, rmlist):
    def testfun(somestring, checklist=rmlist):
        return somestring not in checklist
    mylist = filter(testfun, mylist)
    return mylist


def getFreqTweets(name):
    tweets = getTweets('#'+name)
    words = getwords(tweets)
    freqdist = filterdist_words(words)
    total = 150
    tweet_list = freqdist.keys()[:total]
    count_list = freqdist.values()[:total]
    freqtweets_dict = dict(zip(tweet_list, count_list))
    #print "getFreqTweets",name,freqtweets_dict
    return freqtweets_dict

def getTextFromTweetUrls(name):
    tweetUrlList = getTweetUrls('#'+name)
    textlist = []
    for tweetUrl in tweetUrlList:
        #req = Request(tweetUrl)
        try:
            r = requests.get(tweetUrl)
        except RequestException as e:
            #response = urlopen(req)
            '''
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code

        else:
            html = response.read()
            response.close()
            clean = clean_html(html)
            print tweetUrl, clean
            textlist.append(clean)
        '''
        else:
            print r.text
    return textlist

