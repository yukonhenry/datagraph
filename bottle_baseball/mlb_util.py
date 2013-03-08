from lxml import etree
from collections import namedtuple
import cPickle
import networkx as nx
from networkx.readwrite import json_graph
from twitter_util import getFreqTweets
import simplejson as json
from pprint import pprint

def getMLBteamlist():
    mlb_teamlist = ['ana','ari','atl','bal','bos','chn','cin','cle','col','cha',
                    'det','hou','kca','lan','mia','mil','min','nyn','nya','oak',
                    'phi','pit','sdn','sea','sfn','sln','tba','tex','tor','was']
    return mlb_teamlist

def getMLBteamcode(code):
    teamlist = getMLBteamlist()
    return teamlist[code]

def printTeams():
    print "0 Anaheim"
    print "1 Arizona"
    print "2 Atlanta"
    print "3 Baltimore"
    print "4 Boston"
    print "5 Cubs"
    print "6 Cincinatti"
    print "7 Cleveland"
    print "8 Colorado"
    print "9 White Sox"
    print "10 Detroit"
    print "11 Houston"
    print "12 Kansas City"
    print "13 Dodgers"
    print "14 Miami"
    print "15 Milwaukee"
    print "16 Minnesota"
    print "17 Mets"
    print "18 Yankees"
    print "19 Oakland"
    print "20 Phillies"
    print "21 Pittsburg"
    print "22 San Diego"
    print "23 Seattle"
    print "24 San Francisco"
    print "25 St. Louis"
    print "26 Tampa Bay"
    print "27 Texas"
    print "28 Toronto"
    print "29 Washington"

def getMLBteam_details(tcode):
    #tree = etree.parse("http://mlb.mlb.com/properties/mlb_properties.xml")
    #rootnode = tree.getroot()
    rdoc = cPickle.load(open("/home/henry/workspace/twitterexplore/mlbxml.pickle"))
    doc = etree.fromstring(rdoc)
    teamdata = doc.xpath("/mlb/leagues/league[@club='mlb']/teams/team[@team_code='"+tcode+"']")[0]
    print teamdata.attrib['club_full_name']
    # ref http://stackoverflow.com/questions/2970608/what-are-named-tuples-in-python
    ClubNames = namedtuple('ClubNames', 'common_name twitter_name')
    ClubNames.common_name = teamdata.attrib['club_common_name']
    ClubNames.twitter_name = teamdata.attrib['twitter']
    return ClubNames

def getMLBteamname_list():
    # ref http://infohost.nmt.edu/tcc/help/pubs/pylxml/web/index.html
    # also experiment with source http://mlb.mlb.com/properties/mlb_properties.xml
    fr = open("mlb_team_twitternames.pickle")
    twitterSet = cPickle.load(fr)
    fr.close()
    return twitterSet

def getMLBStoveInfoJSON():
   mlbTwitterBaseSet = getMLBteamname_list()
   G = nx.Graph()
   for team in mlbTwitterBaseSet:
       G.add_node(team)
       freqtweets_dict = getFreqTweets(team)
       freqSet = set(freqtweets_dict.keys())
       selfSet = [team]
       mlbSet = mlbTwitterBaseSet.copy()
       mlbSet.difference_update(selfSet)
       interSet = freqSet.intersection(mlbSet)
       if interSet:
           G.add_weighted_edges_from([(team,x,freqtweets_dict[x]) for x in interSet])
           print "intersection",team, interSet
       else:
           print team, "no intersection"
   print "Graph properties", G.nodes(), G.edges()
   #show edge list
   for line in nx.generate_edgelist(G,data=True):
       print line
   graphdata = json_graph.node_link_data(G)
   print graphdata
   a = json.dumps({"mlbgraph":graphdata})
   return a

#ref http://stackoverflow.com/questions/2835559/python-parsing-file-json
def getMLBStoveInfoJSON_fromfile():
    json_file = open('mlb_twitter_team_graph.txt')
    data = json.load(json_file)
    pprint(data)
    json_file.close()
    return data

def getMLBgen_bloglist():
    blist = ["http://news.yahoo.com/rss/baseball", "http://www.hardballtimes.com/main/content/rss_2.0/",
                          "http://www.baseballbrains.net/blog.html/feed/"]
    return blist

def getMLBteam_blogdict():
    bdict = {'ana':"http://feeds.feedburner.com/Angelswin?format=xml",
             'ari':"http://feeds.feedburner.com/sportsblogs/azsnakepit.xml",
             'atl':"http://feeds.feedburner.com/sportsblogs/talkingchop.xml",
             'bal':"http://feeds.feedburner.com/sportsblogs/camdenchat.xml",
             'bos':"http://feeds.feedburner.com/sportsblogs/overthemonster.xml",
             'chn':"http://feeds.feedburner.com/sportsblogs/bleedcubbieblue.xml",
             'cin':"http://feeds.feedburner.com/sportsblogs/redreporter.xml",
             'cle':"http://feeds.feedburner.com/sportsblogs/letsgotribe.xml",
             'col':"http://feeds.feedburner.com/sportsblogs/purplerow.xml",
             'cha':"http://feeds.feedburner.com/sportsblogs/southsidesox.xml",
             'det':"http://feeds.feedburner.com/sportsblogs/blessyouboys.xml",
             'hou':"http://feeds.feedburner.com/sportsblogs/crawfishboxes.xml",
             'kca':"http://feeds.feedburner.com/sportsblogs/royalsreview.xml",
             'lan':"http://feeds.feedburner.com/sportsblogs/truebluela.xml",
             'mia':"http://feeds.feedburner.com/sportsblogs/fishstripes.xml",
             'mil':"http://feeds.feedburner.com/sportsblogs/brewcrewball.xml",
             'min':"http://feeds.feedburner.com/sportsblogs/twinkietown.xml",
             'nyn':"http://feeds.feedburner.com/sportsblogs/amazinavenue.xml",
             'nya':"http://http://feeds.feedburner.com/LohudYankees"}
    return bdict.values()
#                    'nya','oak',
#                    'phi','pit','sdn','sea','sfn','sln','tba','tex','tor','was'

def getbaseball_genericwords():
    blist = ['baseball','ball','team','game','season','first','second','runs']
    return blist
def getbaseball_statwords():
    slist = ['rbi','k','ip','r','bb','hr','era']
    return slist
def getbaseball_actionwords():
    alist=['hit','pitch','walk']
    return alist
def getbaseball_rolewords():
    rlist = ['player','pitcher','hitter']
    return rlist
