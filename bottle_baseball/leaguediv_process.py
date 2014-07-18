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
from basicfieldtimescheduler import BasicFieldTimeScheduleGenerator
from dbinterface import MongoDBInterface, DB_Col_Type
from leaguedivprep import getAgeGenderDivision, getDivisionData, getLeagueDivInfo, \
     getFieldInfo, getTournAgeGenderDivision
from sched_exporter import ScheduleExporter
from tournamentscheduler import TournamentScheduler
from eliminationscheduler import EliminationScheduler
import logging
from singletonlite import mongoClient
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from schedmaster import SchedMaster
from scheddbinterface import SchedDBInterface
from prefdbinterface import PrefDBInterface
from teamdbinterface import TeamDBInterface
from sched_exceptions import CodeLogicError

_dbInterface = MongoDBInterface(mongoClient)

class RouteLogic:
    '''ref http://stackoverflow.com/questions/8725605/bottle-framework-and-oop-using-method-instead-of-function and
    https://www.artima.com/weblogs/viewpost.jsp?thread=240808
    http://www.jeffknupp.com/blog/2013/11/29/improve-your-python-decorators-explained/
    for decorator related tutorials and integrating bottle with methods.
    '''
    def __init__(self):
        pass

_routelogic_obj = RouteLogic()

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
    rrdbcol_list = _dbInterface.getScheduleCollection(DB_Col_Type.RoundRobin)
    tourndbcol_list = _dbInterface.getScheduleCollection(DB_Col_Type.ElimTourn)
    #cupschedcol_list = _dbInterface.getCupScheduleCollections()
    fielddb_list = _dbInterface.getScheduleCollection(DB_Col_Type.FieldInfo)
    newscheddb_list = _dbInterface.getScheduleCollection(DB_Col_Type.GeneratedSchedule)
    prefdb_list = _dbInterface.getScheduleCollection(DB_Col_Type.PreferenceInfo)
    teamdb_list = _dbInterface.getScheduleCollection(DB_Col_Type.TeamInfo)
    exclusiondb_list = _dbInterface.getScheduleCollection(DB_Col_Type.ExclusionInfo)
    a = json.dumps({"leaguedivinfo":ldata_tuple.dict_list,
                    "creation_time":time.asctime(),
                    "rrdbcollection_list":rrdbcol_list,
                    "fielddb_list": fielddb_list,
                    "tourndbcollection_list":tourndbcol_list,
                    "newscheddb_list":newscheddb_list,
                    "prefdb_list":prefdb_list,
                    "teamdb_list":teamdb_list,
                    "exclusiondb_list":exclusiondb_list})
    return callback_name+'('+a+')'

@route('/getalldivschedule')
def get_alldivSchedule():
    # http://docs.mongodb.org/manual/tutorial/create-a-unique-index/
    # and pymango doc http://api.mongodb.org/python/current/api/pymongo/collection.html#pymongo.collection.Collection.ensure_index
    # http://api.mongodb.org/python/current/api/pymongo/collection.html#pymongo.collection.Collection.create_index
    # apparently the need to create a unique index is not needed if an upsert (see below) call is made.
    # div_schedule_col.create_index([('age', ASCENDING),('div_gen',ASCENDING)], unique=True, dropDups=True)
    callback_name = request.query.callback
    ldata_divinfo = getLeagueDivInfo().dict_list
    total_match_list = []
    for division in ldata_divinfo:
        nt = division['totalteams']
        ng = division['totalgamedays']
        match = MatchGenerator(nt, ng)
        total_match_list.append({'div_id':division['div_id'], 'match_list':match.generateMatchList(), 'numgames_perteam_list':match.numgames_perteam_list, 'gameslotsperday':match.gameslotsperday})
    # get list of connected divisions through field constraints
    #connectedG = json_graph.node_link_graph(ldata['connected_graph'])
    #connected_div_components = connected_components(connectedG)
    fieldtimeSchedule = BasicFieldTimeScheduleGenerator(_dbInterface)
    fieldtimeSchedule.generateSchedule(total_match_list)
    a = json.dumps({"dbstatus":_dbInterface.getSchedStatus()})
    return callback_name+'('+a+')'

@route('/exportschedule')
def exportSchedule():
    callback_name = request.query.callback
    schedExporter = ScheduleExporter(_dbInterface)
    ldata_divinfo = getLeagueDivInfo().dict_list
    for division in ldata_divinfo:
        schedExporter.exportDivTeamSchedules(div_id=division['div_id'], age=division['div_age'], gen=division['div_gen'],
                                             numteams=division['totalteams'])
        schedExporter.exportTeamSchedules(div_id=division['div_id'], age=division['div_age'], gen=division['div_gen'],
                                             numteams=division['totalteams'])
        schedExporter.exportDivSchedules(division['div_id'])
        schedExporter.exportDivSchedulesRefFormat()
    a = json.dumps({"status":'ready'})
    return callback_name+'('+a+')'

@route('/export_rr2013/<tourn_divinfo_col>')
def export_rr2013(tourn_divinfo_col):
    callback_name = request.query.callback
    tournamentSched = TournamentScheduler(mongoClient, tourn_divinfo_col)
    tournamentSched.exportSchedule()
    a = json.dumps({"status":'ready'})
    return callback_name+'('+a+')'

@route('/export_elim2013/<tourn_divinfo_col>')
def export_elim2013(tourn_divinfo_col):
    callback_name = request.query.callback
    elimsched = EliminationScheduler(mongoClient, tourn_divinfo_col)
    elimsched.exportSchedule()
    a = json.dumps({"status":'ready'})
    return callback_name+'('+a+')'

@route('/getcupschedule/<tourn_divinfo_col>')
def getCupSchedule(tourn_divinfo_col):
    callback_name = request.query.callback
    tournamentsched = TournamentScheduler(mongoClient, tourn_divinfo_col)
    tournamentsched.prepGenerate()
    a = json.dumps({"dbstatus":tournamentsched.tdbInterface.dbInterface.getSchedStatus()})
    return callback_name+'('+a+')'

@route('/elimination2013/<tourn_divinfo_col>')
def elimination2013(tourn_divinfo_col):
    callback_name = request.query.callback
    elimsched = EliminationScheduler(mongoClient, tourn_divinfo_col)
    elimsched.generate()
    a = json.dumps({"dbstatus":elimsched.tdbInterface.dbInterface.getSchedStatus()})
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
    divcode = int(request.query.divisioncode)
    divdata = getDivisionData(divcode)
    age = divdata['div_age']
    gender = divdata['div_gen']
    teamdata_list = _dbInterface.findTeamSchedule(age, gender, tid)
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
    fieldschedule_list = _dbInterface.findFieldSchedule(fid)
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
    metrics_list = _dbInterface.getMetrics(div_tuple.age, div_tuple.gender,
                                          divisionData)
    a = json.dumps({'divfield_list':divisionData['divfield_list'], 'metrics':metrics_list})
    return callback_name+'('+a+')'

# create new db collection based on new schedule parameters (currently for tournament format)
@route('/create_newdbcol/<db_type>/<newcol_name>')
def create_newdbcol(db_type, newcol_name):
    callback_name = request.query.callback
    info_data = request.query.info_data
    # variables intended to be scalar ints should be converted from
    # ints that come across as strings over the wire back to int
    config_status = int(request.query.config_status)
    dbInterface = select_db_interface(db_type, newcol_name)
    if db_type in ['rrdb', 'tourndb']:
        dbInterface.writeDB(info_data, config_status)
    elif db_type in ['fielddb', 'prefdb', 'teamdb']:
        # get divinfo parameters associated with fieldinfo obj
        divstr_colname = request.query.divstr_colname
        divstr_db_type = request.query.divstr_db_type
        dbInterface.writeDB(info_data, config_status,
                            divstr_colname=divstr_colname,
                            divstr_db_type=divstr_db_type)
    else:
        raise CodeLogicError("leaguedivprocess:create_newdbcol: db_type not recognized db_type=%s" % (db_type,))
    _routelogic_obj.dbinterface_obj = dbInterface
    a = json.dumps({'test':'divasdf'})
    return callback_name+'('+a+')'

@route('/update_dbcol/<db_type>/<col_name>')
def update_dbcol(db_type, col_name):
    callback_name = request.query.callback
    update_data_str = request.query.update_data
    dbInterface = select_db_interface(db_type, col_name)
    dbInterface.updateDB(update_data_str)
    a = json.dumps({'test':'updateasdf'})
    return callback_name+'('+a+')'

@route('/delete_dbcol/<db_type>/<delcol_name>')
def delete_dbcol(db_type, delcol_name):
    callback_name = request.query.callback
    #db_type = request.query.db_type
    dbInterface = select_db_interface(db_type, delcol_name)
    #rdbInterface = RRDBInterface(mongoClient, delcol_name)
    #rdbInterface.dbInterface.drop_collection()
    dbInterface.drop_collection();
    #schedcol_list = tdbInterface.dbInterface.getScheduleCollection()
    #a = json.dumps({"dbcollection_list":schedcol_list})
    a = json.dumps({'test':'sdg'})
    return callback_name+'('+a+')'

@route('/get_dbcol/<db_type>/<getcol_name>')
def get_dbcol(db_type, getcol_name):
    callback_name = request.query.callback
    dbInterface = select_db_interface(db_type, getcol_name)
    # save as member of global routelogic object to be used in send_delta function
    _routelogic_obj.dbinterface_obj = dbInterface
    if db_type == 'newscheddb':
        return_obj = {'param_obj':dbInterface.getschedule_param()}
    else:
        dbtuple = dbInterface.readDB();
        info_list = dbtuple.list
        config_status = dbtuple.config_status
        return_obj = {'info_list':info_list, 'config_status':config_status}
        if db_type in ['fielddb', 'prefdb', 'teamdb']:
            # if db is fielddb, then append divinfo information also-
            # used as part of fieldinfo config on UI grid
            divstr_colname = dbtuple.divstr_colname
            divstr_db_type = dbtuple.divstr_db_type
            if divstr_colname and divstr_db_type:
                dbInterface = select_db_interface(divstr_db_type, divstr_colname)
                dbtuple = dbInterface.readDB();
                info_list = dbtuple.list
                config_status = dbtuple.config_status
            else:
                info_list = []
                config_status = 0
                divstr_db_type = ""
                divstr_colname = ""
            divstr_obj = {'colname':divstr_colname, 'db_type':divstr_db_type,
                'info_list':info_list, 'config_status':config_status}
            return_obj.update({'divstr_obj':divstr_obj})
    a = json.dumps(return_obj)
    return callback_name+'('+a+')'

@route('/get_scheddbcol/<getcol_name>')
def get_scheddbcol(getcol_name):
    callback_name = request.query.callback
    divcode = int(request.query.divisioncode)
    # revisit whether this call should be made against RRDBInterface
    # or TournDBInterface
    div = getTournAgeGenderDivision(divcode)
    tdbInterface = TournDBInterface(mongoClient, getcol_name)
    game_list = tdbInterface.readSchedDB(div.age, div.gender)
    a = json.dumps({'game_list':game_list})
    return callback_name+'('+a+')'

@route('/update_fieldtimes/<col_name>')
def update_fieldtimes(col_name):
    callback_name = request.query.callback
    fieldtime_str = request.query.fieldtime_str
    fdbInterface = FieldDBInterface(mongoClient, col_name)
    fdbInterface.updateFieldTimes(fieldtime_str)
    a = json.dumps({'test':'dfh'})
    return callback_name+'('+a+')'

@route('/send_generate')
def send_generate():
    callback_name = request.query.callback
    db_type = request.query.db_type
    divcol_name = request.query.divcol_name
    fieldcol_name = request.query.fieldcol_name
    prefcol_name = request.query.prefcol_name
    schedcol_name = request.query.schedcol_name
    schedMaster = SchedMaster(mongoClient, db_type, divcol_name, fieldcol_name,
        prefcol_name, schedcol_name)
    # save schedMaster to global obj to reuse on get_schedule
    _routelogic_obj.schedmaster_obj = schedMaster
    dbstatus = schedMaster.generate()
    a = json.dumps({"dbstatus":dbstatus})
    return callback_name+'('+a+')'

@route('/send_delta/<action_type>/<field_id:int>')
def send_delta(action_type, field_id):
    callback_name = request.query.callback
    dbInterface = _routelogic_obj.dbinterface_obj
    if action_type == 'remove':
        remove_str = request.query.remove_str
        remove_list = [int(x) for x in remove_str.split(',')]
        # get dbinterface_obj assigned during create_newdbcol
        # send_data is always called from UI config grid, which generates either a
        # create_newdbcol or get_dbcol
        dbstatus = dbInterface.adjust_config(action_type, field_id, remove_list)
    elif action_type == 'change':
        change_str = request.query.change_str
        change_list = json.loads(change_str)
        dbstatus = dbInterface.adjust_config(action_type, field_id, change_list)
    a = json.dumps({"dbstatus":dbstatus})

@route('/get_schedule/<schedcol_name>/<idproperty>/<propid:int>')
def get_schedule(schedcol_name, idproperty, propid):
    callback_name = request.query.callback
    schedMaster = _routelogic_obj.schedmaster_obj
    if schedMaster.schedcol_name == schedcol_name:
        if idproperty == 'team_id' or idproperty == 'fair_id':
            # read query parameters if idprop is team_id - div_age and div_gen
            div_age = request.query.div_age
            div_gen = request.query.div_gen
            return_dict = schedMaster.get_schedule(idproperty, propid,
                div_age=div_age, div_gen=div_gen)
        else:
            return_dict = schedMaster.get_schedule(idproperty, propid)
    else:
        return_dict = {}
    a = json.dumps(return_dict)
    return callback_name+'('+a+')'

def select_db_interface(db_type, colname):
    if db_type == 'rrdb':
        dbInterface = RRDBInterface(mongoClient, colname)
    elif db_type == 'tourndb':
        dbInterface = TournDBInterface(mongoClient, colname)
    elif db_type == 'fielddb':
        dbInterface = FieldDBInterface(mongoClient, colname)
    elif db_type == 'newscheddb':
        dbInterface = SchedDBInterface(mongoClient, colname)
    elif db_type == 'prefdb':
        dbInterface = PrefDBInterface(mongoClient, colname)
    elif db_type == 'teamdb':
        dbInterface = TeamDBInterface(mongoClient, colname)
    else:
        raise CodeLogicError("leaguedivprocess:get_dbcol: db_type not recognized db_type=%s" % (db_type,))
        dbInterface = None
    return dbInterface
