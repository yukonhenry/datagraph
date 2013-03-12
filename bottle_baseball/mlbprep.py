#!/usr/bin/python
from lxml import etree
import cPickle
from mlb_util import getMLBStoveInfoJSON
from urllib2 import urlopen

# find twitter names for each mlb team and store it in a pickle
# ref see bug http://stackoverflow.com/questions/6199666/lxml-only-loading-a-single-network-entity-before-raising-xmlsyntaxerror# for use of urllib2
tree = etree.parse(urlopen("http://mlb.mlb.com/properties/mlb_properties.xml"))
rootnode = tree.getroot()
f = open("mlbxml.pickle","wb")
cPickle.dump(etree.tostring(rootnode),f)
f.close()
teams = rootnode.xpath("/mlb/leagues/league[@club='mlb']/teams")[0].findall('team')
twitter_list = []
for team in teams:
    twitter_list.append(team.get('twitter'))
twitterSet = set(twitter_list)
f = open("/home/henry/workspace/datagraph/bottle_baseball/mlb_team_twitternames.pickle","wb")
cPickle.dump(twitterSet, f)
f.close()

# use primarily for testing below as it takes too long
# to construct relationship tweet graph for mlb teams
# based on team correlation through twitter
f = open('/home/henry/workspace/datagraph/bottle_baseball/mlb_twitter_team_graph.txt','w')
f.write(getMLBStoveInfoJSON())
f.close()



