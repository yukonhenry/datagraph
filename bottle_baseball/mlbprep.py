#!/usr/bin/python
from lxml import etree
import cPickle
from mlb_util import getMLBStoveInfoJSON
from urllib2 import urlopen
import simplejson as json

# find twitter names for each mlb team and store it in a pickle
# ref see bug http://stackoverflow.com/questions/6199666/lxml-only-loading-a-single-network-entity-before-raising-xmlsyntaxerror# for use of urllib2
tree = etree.parse(urlopen("http://mlb.mlb.com/properties/mlb_properties.xml"))
rootnode = tree.getroot()
f = open("mlbxml.pickle","wb")
cPickle.dump(etree.tostring(rootnode),f)
f.close()
'''
teams = rootnode.xpath("/mlb/leagues/league[@club='mlb']/teams")[0].findall('team')
mlb_twitter_dict = {}
for team in teams:
    teamname_list = []
    teamname_list.append(team.get('facebook'))
    teamname_list.append(team.get('club_common_name'))
    #key is twitter name, followed by list of other recognizable names
    mlb_twitter_dict[team.get('twitter')] = teamname_list
a = json.dumps(mlb_twitter_dict)
print "team name list in mlbprep", a
f = open('mlb_team_names_json.txt','w')
f.write(a)
f.close()
'''
# use primarily for testing below as it takes too long
# to construct relationship tweet graph for mlb teams
# based on team correlation through twitter
f = open('mlb_twitter_team_graph.txt','w')
f.write(getMLBStoveInfoJSON())
f.close()



