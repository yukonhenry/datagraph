#!/usr/bin/python
''' Copyright YukonTR 2013 '''
import simplejson as json
import time
from pprint import pprint
from bottle import route, request
import networkx as nx
from networkx.readwrite import json_graph
from networkx import connected_components
from matchgenerator import MatchGenerator
from fieldtimescheduler import FieldTimeScheduleGenerator
from dbinterface import MongoDBInterface
from leaguedivprep import getAgeGenderDivision, getDivisionData, getLeagueDivInfo, \
     getFieldInfo
from sched_exporter import ScheduleExporter
from tournamentscheduler import TournamentScheduler
import logging
from singletonlite import mongoClient
from tourndbinterface import TournDBInterface

dbInterface = MongoDBInterface(mongoClient)

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
    ldata_tuple = getLeagueDivInfo()
    field_tuple = getFieldInfo()
    dbstatus = dbInterface.getSchedStatus()
    schedcol_list = dbInterface.getScheduleCollections()
    cupschedcol_list = dbInterface.getCupScheduleCollections()
    logging.info("leaguedivprocess:leaguedivinfo:dbstatus=%d",dbstatus)
    a = json.dumps({"leaguedivinfo":ldata_tuple.dict_list,
                    "field_info":field_tuple.dict_list,
                    "creation_time":time.asctime(),
                    "dbstatus":dbstatus,
                    "dbcollection_list":schedcol_list,
                    "cupdbcollection_list":cupschedcol_list})
    return callback_name+'('+a+')'

# Get per-division schedule
@route('/leaguedivinfo/<tid:int>', method='GET')
def leaguedivinfo(tid):
    callback_name = request.query.callback
    ldata_tuple = getLeagueDivInfo()
    ldata_divinfo = ldata_tuple.dict_list
    leaguediv_indexerGet = ldata_tuple.indexerGet
    divindex = leaguediv_indexerGet(tid)
    if divindex is not None:
        div = ldata_divinfo[divindex]
        age = div['agediv']
        gender = div['gender']
        game_list = dbInterface.findDivisionSchedule(age, gender)
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
    ldata_divinfo = getLeagueDivInfo().dict_list
    total_match_list = []
    for division in ldata_divinfo:
        nt = division['totalteams']
        ng = division['gamesperseason']
        match = MatchGenerator(nt, ng)
        total_match_list.append({'div_id':division['div_id'], 'match_list':match.generateMatchList(),
                                 'numgames_list':match.numGames_list, 'gameslotsperday':match.gameslotsperday})
    # get list of connected divisions through field constraints
    #connectedG = json_graph.node_link_graph(ldata['connected_graph'])
    #connected_div_components = connected_components(connectedG)
    fieldtimeSchedule = FieldTimeScheduleGenerator(dbInterface)
    fieldtimeSchedule.generateSchedule(total_match_list)
    a = json.dumps({"dbstatus":dbInterface.getSchedStatus()})
    return callback_name+'('+a+')'

@route('/exportschedule')
def exportSchedule():
    callback_name = request.query.callback
    schedExporter = ScheduleExporter(dbInterface)
    ldata_divinfo = getLeagueDivInfo().dict_list
    for division in ldata_divinfo:
        schedExporter.exportDivTeamSchedules(div_id=division['div_id'], age=division['agediv'], gen=division['gender'],
                                             numteams=division['totalteams'])
        schedExporter.exportTeamSchedules(div_id=division['div_id'], age=division['agediv'], gen=division['gender'],
                                             numteams=division['totalteams'])
        schedExporter.exportDivSchedules(division['div_id'])
        schedExporter.exportDivSchedulesRefFormat()
    a = json.dumps({"status":'ready'})
    return callback_name+'('+a+')'

@route('/getcupschedule/<tourn_divinfo_col>')
def getCupSchedule(tourn_divinfo_col):
    callback_name = request.query.callback
    field_tuple = getFieldInfo()
    tournamentsched = TournamentScheduler(mongoClient, tourn_divinfo_col, field_tuple)
    tournamentsched.prepGenerate()
    a = ""
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
    metrics_list = dbInterface.getMetrics(div_tuple.age, div_tuple.gender,
                                          divisionData)
    a = json.dumps({'fields':divisionData['fields'], 'metrics':metrics_list})
    return callback_name+'('+a+')'

# create new db collection based on new schedule parameters (currently for tournament format)
@route('/create_newdbcol/<newcol_name>')
def create_newdbcol(newcol_name):
    callback_name = request.query.callback
    divinfo_data = request.query.divinfo_data
    tdbInterface = TournDBInterface(mongoClient, newcol_name)
    tdbInterface.writeDB(divinfo_data)
    a = json.dumps({'test':'asdf'})
    return callback_name+'('+a+')'

@route('/delete_dbcol/<delcol_name>')
def delete_dbcol(delcol_name):
    callback_name = request.query.callback
    print 'delete', delcol_name
    a = json.dumps({'test':'werjler'})
    return callback_name+'('+a+')'

@route('/get_dbcol/<getcol_name>')
def get_dbcol(getcol_name):
    callback_name = request.query.callback
    tdbInterface = TournDBInterface(mongoClient, getcol_name)
    divinfo_list = tdbInterface.readDB()
    a = json.dumps({'divinfo_list':divinfo_list})
    return callback_name+'('+a+')'
