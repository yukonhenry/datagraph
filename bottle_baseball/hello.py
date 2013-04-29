#!/usr/bin/python
from bottle import route, request, run
#ref http://simplejson.readthedocs.org/en/latest/
import simplejson as json
import sys
import networkx as nx
from networkx.readwrite import json_graph
# sys.path.append('/home/henry/workspace/twitterexplore')
from mlb_util import getMLBteam_details, getMLBteamname_list, getMLBStoveInfoJSON, getMLBStoveInfoJSON_fromfile
from twitter_util import getTweets, getTweetUrls, getTextFromTweetUrls, getFreqTweets
from cacooparse import getCacooDesignJSON
import time
from scheduler import generateRRSchedule
from leaguediv_process import *

# if one of the module is reworked, don't forget to invoke 'reload(module)' cmd
@route('/hello')
def hello():
    # follow jsonp format
    hello_call = request.query.callback
    ret_type = request.query.ret_type
    if (request.query.team_code):  #checking for None does not work
        teamCode = request.query.team_code
        teamName = getMLBteam_details(teamCode)
        tname = teamName.twitter_name
        print teamCode, teamName.common_name, teamName.twitter_name
        if (ret_type == "tweet_url"):
            urltext_list = getTextFromTweetUrls(tname)
            a = json.dumps({"team_search":urltext_list})
        else:
            freqwords_dict = getFreqTweets(tname)   # element  is words (keys)
            freqwords = freqwords_dict.keys()
            if (ret_type == "team_relation"):
                freqSet = set(freqwords)
                # ref http://en.wikibooks.org/wiki/Python_Programming/Sets for python set operations
                selfSet = [tname]
                twitterSet = getMLBteamname_list()
                twitterSet.difference_update(selfSet) #remove own team
                interSet = freqSet.intersection(twitterSet)

                DG = nx.DiGraph()
                DG.add_node(tname)
                if interSet:
                    print interSet
                    DG.add_nodes_from(interSet)
                    DG.add_edges_from([tname,x] for x in interSet)
                else:
                    print "no intersection"
                # ref http://networkx.github.com/documentation/latest/reference/readwrite.json_graph.html
                data = json_graph.tree_data(DG,root=tname)
                a = json.dumps({"team_search":data})
                #            a = json.dumps({"team_search":{"id":tname, \
                #                                           "contents":[{"id":"abc","contents":[]},\
                #                                                       {"id":"cded","contents":[]}]}})
            else:
                a = json.dumps({"team_search":freqwords})
        #return hello_call+'('+a+');'
    else:
        term = request.query.general
        print term, ret_type
        if (ret_type == "tweet_raw"):
            tweets = getTweets(term)
        elif (ret_type == "tweet_url"):
            tweets = getTweetUrls(term)
        else:
            tweets = []
        a = json.dumps({"tweet_list":tweets}, indent=3)
        #return hello_call+'('+a+');'
    return hello_call+'('+a+');'

@route('/getdesign')
def getdesign():
    a = getCacooDesignJSON()
    getdesign_call = request.query.callback
    return getdesign_call+'('+a+');'

@route('/getdesign1')
def getdesign1():
    print "getdesign1 called"
    return json.dumps({"name":"aok"})

@route('/getmlbstoveinfo')
def getMLBStoveInfo():
    #a = getMLBStoveInfoJSON()
    a = json.dumps(getMLBStoveInfoJSON_fromfile())
    callback_name = request.query.callback
    return callback_name+'('+a+');'

@route('/getpathdata')
def getpathdata():
    a = json.dumps({"creation_time":time.asctime(),"pathdata":[[20,20],[150,150]]})
    callback_name = request.query.callback
    sg_nodes = json.loads(request.query.sg_nodes)
    obs_polyline = json.loads(request.query.obs_poly)
    print "nodes=",sg_nodes, len(sg_nodes)
    print "obstacle=",obs_polyline, len(obs_polyline)
    return callback_name+'('+a+');'

@route('/getschedule')
def getschedule():
    callback_name = request.query.callback
    numTeams = request.query.num_teams
    numVenues = request.query.num_venues
    game_list = generateRRSchedule(int(numTeams), int(numVenues))
    a = json.dumps({"game_list":game_list})
    return callback_name+'('+a+');'

run(host='localhost', port=8080, debug=True)

