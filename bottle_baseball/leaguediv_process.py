#!/usr/bin/python
import simplejson as json
from pprint import pprint
from bottle import route, request
import networkx as nx
from networkx.readwrite import json_graph
from networkx import connected_components
from matchgenerator import MatchGenerator
from fieldtimescheduler import FieldTimeScheduleGenerator
from dbinterface import MongoDBInterface
from leaguedivprep import getAgeGenderDivision, getDivisionData
'''
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
# prep for connecting to db
client = MongoClient()
testschedule_db = client.testschedule_db
div_schedule_col = testschedule_db.div_schedule
# create collection in db for storing metrics
metrics_collect = testschedule_db.metrics
'''
dbInterface = MongoDBInterface()

def get_leaguedata():
    fname = 'leaguediv_json.txt'
    json_file = open(fname)
    ldata = json.load(json_file)
    #pprint(ldata)
    json_file.close()
    return ldata

'''
references
http://www.tutorial.useiis7.net/dojodoc/001/
http://myadventuresincoding.wordpress.com/2011/01/02/creating-a-rest-api-in-python-using-bottle-and-mongodb/
http://gotofritz.net/blog/weekly-challenge/restful-python-api-bottle/
http://bottlepy.org/docs/dev/tutorial.html#request-routing
'''
@route('/leaguedivinfo')
def leaguedivinfo_all():
    callback_name = request.query.callback
    ldata = get_leaguedata()
    a = json.dumps(ldata)
    return callback_name+'('+a+')'

# Get per-division schedule
@route('/leaguedivinfo/<tid:int>', method='GET')
def leaguedivinfo(tid):
    callback_name = request.query.callback
    ldata = get_leaguedata()
    ldata_divinfo = ldata['leaguedivinfo']
    # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
    leaguediv_indexer = dict((p['div_id'],i) for i,p in enumerate(ldata_divinfo))
    divindex = leaguediv_indexer.get(tid)
    if divindex is not None:
        div = ldata_divinfo[divindex]
        age = div['agediv']
        gender = div['gender']
        game_list = dbInterface.findDivisionSchedule(age, gender)
        #metrics_data = metrics_collect.find_one({'age':age, 'gender':gender})
        #metrics_list = metrics_data['metrics_list']
        #print metrics_list
        a = json.dumps({"game_list":game_list, "fields":div['fields']})
        return callback_name+'('+a+')'
    else:
        return False

@route('/getalldivschedule')
def get_alldivSchedule():
    # http://docs.mongodb.org/manual/tutorial/create-a-unique-index/
    # and pymango doc http://api.mongodb.org/python/current/api/pymongo/collection.html#pymongo.collection.Collection.ensure_index
    # http://api.mongodb.org/python/current/api/pymongo/collection.html#pymongo.collection.Collection.create_index
    # apparently the need to create a unique index is not needed if an upsert (see below) call is made.
    # div_schedule_col.create_index([('age', ASCENDING),('gender',ASCENDING)], unique=True, dropDups=True)
    callback_name = request.query.callback
    ldata = get_leaguedata()
    ldata_divinfo = ldata['leaguedivinfo']
    total_match_list = []
    for division in ldata_divinfo:
        nt = division['totalteams']
        ng = division['gamesperseason']
        match = MatchGenerator(nt, ng)
        total_match_list.append({'div_id':division['div_id'], 'match_list':match.generateMatchList(), 'numgames_list':match.numGames_list, 'gameslotsperday':match.gameslotsperday})
    # get list of connected divisions through field constraints
    #connectedG = json_graph.node_link_graph(ldata['connected_graph'])
    #connected_div_components = connected_components(connectedG)
    fieldtimeSchedule = FieldTimeScheduleGenerator(ldata_divinfo, ldata['field_info'],
                                                   dbInterface)
    fieldtimeSchedule.generateSchedule(total_match_list)
    print 'aok'
    a = json.dumps({"status":'ready'})
    return callback_name+'('+a+')'

@route('/divisiondata/<did:int>', method='GET')
def divisiondata(did):
    callback_name = request.query.callback
    division = getDivisionData(did)
    numTeams = division['totalteams']
    a = json.dumps({'totalteams':numTeams})
    return callback_name+'('+a+')'

@route('/teamdata/<tid:int>', method='GET')
def teamdata(tid):
    callback_name = request.query.callback
    # divcode is 0-index based; see html and js code
    divcode = int(request.query.division_code)
    divdata = getDivisionData(divcode)
    age = divdata['agediv']
    gender = divdata['gender']
    teamdata_list = dbInterface.findTeamSchedule(age, gender, tid)
    # http://stackoverflow.com/questions/13708857/mongodb-aggregation-framework-nested-arrays-subtract-expression
    # http://docs.mongodb.org/manual/reference/aggregation/
    #col.aggregate({$match:{age:'U12',gender:'G'}},{$project:{game_list:1}},{$unwind:"$game_list"},{$unwind:"$game_list.GAMEDAY_DATA"},{$unwind:"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"},{$match:{$or:[{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.GAME_LIST.HOME':1},{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.GAME_LIST.AWAY':1}]}})
    '''
    result_list = div_schedule_col.aggregate([{"$match":{'age':age,'gender':gender}},
                                            {"$project":{'game_list':1}},
                                            {"$unwind":"$game_list"},
                                            {"$unwind":"$game_list.GAMEDAY_DATA"},
                                            {"$unwind":"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"},
                                            {"$match":{"$or":[{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.GAME_TEAM.HOME':tid},
                                                              {'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.GAME_TEAM.AWAY':tid}]}}])

'''
    a = json.dumps({'teamdata_list':teamdata_list})
    return callback_name+'('+a+')'

@route('/fieldschedule/<fid:int>', method='GET')
def fieldschedule(fid):
    callback_name = request.query.callback
    fieldschedule_list = dbInterface.findFieldSchedule(fid)
    a = json.dumps({'fieldschedule_list':fieldschedule_list})
    return callback_name+'('+a+')'

    '''
    # mongo shell aggregate command
    # col.aggregate({$unwind:"$game_list"},{$unwind:"$game_list.GAMEDAY_DATA"},{$unwind:"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"}, {$match:{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.VENUE':8}})
    result_list = div_schedule_col.aggregate([{"$unwind":"$game_list"},
                                              {"$unwind":"$game_list.GAMEDAY_DATA"},
                                              {"$unwind":"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"},
                                              {"$match":{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.VENUE':fid}},
                                              {"$sort":{'game_list.GAMEDAY_ID':1,'game_list.GAMEDAY_DATA.START_TIME':1}}])
'''

@route('/schedulemetrics/<div_id:int>', method='GET')
def schedulemetrics(div_id):
    callback_name = request.query.callback
    divisionData = getDivisionData(div_id)
    div_tuple = getAgeGenderDivision(div_id)
    metrics_list = dbInterface.getMetrics(div_id, div_tuple.age, div_tuple.gender,
                                          divisionData)
    a = json.dumps({'fields':divisionData['fields'], 'metrics':metrics_list})
    return callback_name+'('+a+')'
