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
from leaguedivprep import getDivisionData, getTournAgeGenderDivision
from sched_exporter import ScheduleExporter
from tournamentscheduler import TournamentScheduler
from eliminationscheduler import EliminationScheduler
import logging
from singletonlite import mongoClient, hostserver, generic_dbInterface, creation_time
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from schedmaster import SchedMaster
from scheddbinterface import SchedDBInterface
from prefdbinterface import PrefDBInterface
from teamdbinterface import TeamDBInterface
from conflictdbinterface import ConflictDBInterface
from userdbinterface import UserDBInterface
from sched_exceptions import CodeLogicError
from xls_exporter import XLS_Exporter

#_dbInterface = MongoDBInterface(mongoClient)

class RouteLogic:
    '''ref http://stackoverflow.com/questions/8725605/bottle-framework-and-oop-using-method-instead-of-function and
    https://www.artima.com/weblogs/viewpost.jsp?thread=240808
    http://www.jeffknupp.com/blog/2013/11/29/improve-your-python-decorators-explained/
    for decorator related tutorials and integrating bottle with methods.
    '''
    def __init__(self):
        self.dbinterface_map = dict();
        self.schedmaster_map = dict();

_routelogic_obj = RouteLogic()

'''
references
http://www.tutorial.useiis7.net/dojodoc/001/
http://myadventuresincoding.wordpress.com/2011/01/02/creating-a-rest-api-in-python-using-bottle-and-mongodb/
http://gotofritz.net/blog/weekly-challenge/restful-python-api-bottle/
http://bottlepy.org/docs/dev/tutorial.html#request-routing
'''

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

    '''
    # mongo shell aggregate command
    # col.aggregate({$unwind:"$game_list"},{$unwind:"$game_list.GAMEDAY_DATA"},{$unwind:"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"}, {$match:{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.VENUE':8}})
    result_list = div_schedule_col.aggregate([{"$unwind":"$game_list"},
                                              {"$unwind":"$game_list.GAMEDAY_DATA"},
                                              {"$unwind":"$game_list.GAMEDAY_DATA.VENUE_GAME_LIST"},
                                              {"$match":{'game_list.GAMEDAY_DATA.VENUE_GAME_LIST.VENUE':fid}},
                                              {"$sort":{'game_list.GAMEDAY_ID':1,'game_list.GAMEDAY_DATA.START_TIME':1}}])
'''

# create new db collection based on new schedule parameters (currently for tournament format)
@route('/create_newdbcol/<userid_name>/<db_type>/<newcol_name>')
def create_newdbcol(userid_name, db_type, newcol_name):
    callback_name = request.query.callback
    info_data = request.query.info_data
    # variables intended to be scalar ints should be converted from
    # ints that come across as strings over the wire back to int
    config_status = int(request.query.config_status)
    dbInterface = select_db_interface(userid_name, db_type, newcol_name)
    if db_type in ['rrdb', 'tourndb']:
        oddnum_mode = int(request.query.oddnum_mode)
        dbInterface.writeDB(info_data, config_status, oddnum_mode)
    elif db_type in ['fielddb', 'prefdb', 'teamdb', 'conflictdb']:
        # get divinfo parameters associated with fieldinfo obj
        divstr_colname = request.query.divstr_colname
        divstr_db_type = request.query.divstr_db_type
        dbInterface.writeDB(info_data, config_status,
                            divstr_colname=divstr_colname,
                            divstr_db_type=divstr_db_type)
    else:
        raise CodeLogicError("leaguedivprocess:create_newdbcol: db_type not recognized db_type=%s" % (db_type,))
    _routelogic_obj.dbinterface_map[userid_name] = dbInterface
    a = json.dumps({'test':'divasdf'})
    return callback_name+'('+a+')'

@route('/update_dbcol/<userid_name>/<db_type>/<col_name>')
def update_dbcol(userid_name, db_type, col_name):
    callback_name = request.query.callback
    update_data_str = request.query.update_data
    dbInterface = select_db_interface(userid_name, db_type, col_name)
    dbInterface.updateDB(update_data_str)
    a = json.dumps({'test':'updateasdf'})
    return callback_name+'('+a+')'

@route('/delete_dbcol/<userid_name>/<db_type>/<delcol_name>')
def delete_dbcol(userid_name, db_type, delcol_name):
    callback_name = request.query.callback
    dbInterface = select_db_interface(userid_name, db_type, delcol_name)
    dbInterface.drop_collection();
    a = json.dumps({'test':'sdg'})
    return callback_name+'('+a+')'

@route('/get_dbcol/<userid_name>/<db_type>/<getcol_name>')
def get_dbcol(userid_name, db_type, getcol_name):
    callback_name = request.query.callback
    dbInterface = select_db_interface(userid_name, db_type, getcol_name)
    # save as member of global routelogic object to be used in send_delta function
    _routelogic_obj.dbinterface_map[userid_name] = dbInterface
    if db_type == 'newscheddb':
        return_obj = {'param_obj':dbInterface.getschedule_param(),
        'sched_status':dbInterface.getsched_status()}
    else:
        dbtuple = dbInterface.readDB();
        info_list = dbtuple.list
        config_status = dbtuple.config_status
        return_obj = {'info_list':info_list, 'config_status':config_status}
        if db_type in ['fielddb', 'prefdb', 'teamdb', 'conflictdb']:
            # if db is fielddb, then append divinfo information also-
            # used as part of fieldinfo config on UI grid
            divstr_colname = dbtuple.divstr_colname
            divstr_db_type = dbtuple.divstr_db_type
            if divstr_colname and divstr_db_type:
                dbInterface = select_db_interface(userid_name, divstr_db_type, divstr_colname)
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

@route('/send_generate/<userid_name>')
def send_generate(userid_name):
    callback_name = request.query.callback
    db_type = request.query.db_type
    divcol_name = request.query.divcol_name
    fieldcol_name = request.query.fieldcol_name
    schedcol_name = request.query.schedcol_name
    prefcol_name = request.query.prefcol_name
    conflictcol_name = request.query.conflictcol_name
    schedMaster = SchedMaster(mongoClient, userid_name, db_type, divcol_name,
        fieldcol_name, schedcol_name, prefcol_name=prefcol_name,
        conflictcol_name=conflictcol_name)
    if not schedMaster.error_code:
        # save schedMaster to global obj to reuse on get_schedule
        _routelogic_obj.schedmaster_map[userid_name] = schedMaster
        dbstatus = schedMaster.generate()
        a = json.dumps({"dbstatus":dbstatus})
    else:
        a = json.dumps({"error_code":schedMaster._error_code})
        del schedMaster
    return callback_name+'('+a+')'

@route('/send_delta/<userid_name>/<action_type>/<field_id:int>')
def send_delta(userid_name, action_type, field_id):
    callback_name = request.query.callback
    dbInterface = _routelogic_obj.dbinterface_map[userid_name]
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

@route('/get_schedule/<userid_name>/<schedcol_name>/<idproperty>/<propid:int>')
def get_schedule(userid_name, schedcol_name, idproperty, propid):
    callback_name = request.query.callback
    schedMaster = _routelogic_obj.schedmaster_map.get(userid_name)
    if schedMaster is None:
        dbInterface = SchedDBInterface(mongoClient, userid_name, schedcol_name)
        param = dbInterface.getschedule_param()
        schedMaster = SchedMaster(mongoClient, userid_name, param['divdb_type'],
            param['divcol_name'], param['fieldcol_name'], schedcol_name,
            prefcol_name=param['prefcol_name'],
            conflictcol_name=param['conflictcol_name'])
        if not schedMaster.error_code:
            # save schedMaster to global obj to reuse on get_schedule
            _routelogic_obj.schedmaster_map[userid_name] = schedMaster
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

@route('/get_xls/<userid_name>/<schedcol_name>/<genxls_id>')
def get_xls(userid_name, schedcol_name, genxls_id):
    callback_name = request.query.callback
    schedMaster = _routelogic_obj.schedmaster_map.get(userid_name)
    if schedMaster is None:
        dbInterface = SchedDBInterface(mongoClient, userid_name, schedcol_name)
        param = dbInterface.getschedule_param()
        schedMaster = SchedMaster(mongoClient, userid_name, param['divdb_type'],
            param['divcol_name'], param['fieldcol_name'], schedcol_name,
            prefcol_name=param['prefcol_name'],
            conflictcol_name=param['conflictcol_name'])
        if not schedMaster.error_code:
            # save schedMaster to global obj to reuse on get_schedule
            _routelogic_obj.schedmaster_map[userid_name] = schedMaster
    if schedMaster.schedcol_name == schedcol_name:
        xls_exporter = schedMaster.xls_exporter
        if xls_exporter is None:
            xls_exporter = XLS_Exporter(schedcol_name,
                divinfo_tuple=schedMaster.divinfo_tuple,
                fieldinfo_tuple=schedMaster.fieldinfo_tuple,
                sdbInterface=schedMaster.sdbInterface)
            schedMaster.xls_exporter = xls_exporter
        file_list = xls_exporter.export(genxls_id)
        return_dict = {'file_list':file_list}
    else:
        return_dict = {}
    a = json.dumps(return_dict)
    return callback_name+'('+a+')'

@route('/get_hostserver')
def get_hostserver():
    callback_name = request.query.callback
    a = json.dumps({"hostserver":hostserver, "creation_time":creation_time})
    return callback_name+'('+a+')'

@route('/check_user/<userid_name>')
def check_user(userid_name):
    callback_name = request.query.callback
    dbInterface = UserDBInterface(mongoClient)
    result = dbInterface.check_user(userid_name)
    #userdb_list = generic_dbInterface.getUserCollection()
    #result = 1 if userid_name in userdb_list else 0
    a = json.dumps({'result':result})
    return callback_name+'('+a+')'

@route('/create_user/<userid_name>')
def create_user(userid_name):
    callback_name = request.query.callback
    dbInterface = UserDBInterface(mongoClient)
    dbInterface.writeDB(userid_name)
    #dbInterface.simplewriteDB(userid_name)
    a = json.dumps({'result':1})
    return callback_name+'('+a+')'

@route('/get_dbcollection/<userid_name>')
def get_dbcollection(userid_name):
    callback_name = request.query.callback
    rrdbcol_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.RoundRobin, userid_name)
    tourndbcol_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.ElimTourn, userid_name)
    #cupschedcol_list = generic_dbInterface.getCupScheduleCollections(, userid_name)
    fielddb_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.FieldInfo, userid_name)
    newscheddb_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.GeneratedSchedule, userid_name)
    prefdb_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.PreferenceInfo, userid_name)
    teamdb_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.TeamInfo, userid_name)
    conflictdb_list = generic_dbInterface.getScheduleCollection(
        DB_Col_Type.ConflictInfo, userid_name)
    a = json.dumps({"rrdbcollection_list":rrdbcol_list,
                    "fielddb_list": fielddb_list,
                    "tourndbcollection_list":tourndbcol_list,
                    "newscheddb_list":newscheddb_list,
                    "prefdb_list":prefdb_list,
                    "teamdb_list":teamdb_list,
                    "conflictdb_list":conflictdb_list})
    return callback_name+'('+a+')'

def select_db_interface(userid_name, db_type, colname):
    if db_type == 'rrdb':
        dbInterface = RRDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'tourndb':
        dbInterface = TournDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'fielddb':
        dbInterface = FieldDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'newscheddb':
        dbInterface = SchedDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'prefdb':
        dbInterface = PrefDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'teamdb':
        dbInterface = TeamDBInterface(mongoClient, userid_name, colname)
    elif db_type == 'conflictdb':
        dbInterface = ConflictDBInterface(mongoClient, userid_name, colname)
    else:
        raise CodeLogicError("leaguedivprocess:select_db_interface: db_type not recognized db_type=%s" % (db_type,))
        dbInterface = None
    return dbInterface
