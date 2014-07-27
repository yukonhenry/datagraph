#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface
import simplejson as json
from collections import namedtuple
import logging
gameday_id_CONST = 'GAMEDAY_ID'
start_time_CONST = 'START_TIME'
# global for namedtuple
_List_Status = namedtuple('_List_Status', 'list config_status')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class RRDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, newcol_name,
            DB_Col_Type.RoundRobin, 'DIV_ID')

    def writeDB(self, divinfo_str, config_status):
        divinfo_list = json.loads(divinfo_str)
        document_list = [{k.upper():v for k,v in x.items()} for x in divinfo_list]
        self.dbinterface.updateInfoDocument(document_list, config_status, 'DIV_ID')

    def updateDB(self, update_data_str):
        # right now this update operation is hardcoded to update divfield_list only
        update_data_list = json.loads(update_data_str)
        for update_obj in update_data_list:
            query_obj = {'DIV_ID':update_obj['div_id']}
            operator_obj = {"DIVFIELD_LIST":update_obj['divfield_list']}
            self.dbinterface.updatedoc(query_obj, "$set", operator_obj)

    def readDB(self):
        liststatus_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = liststatus_tuple.list
        for div in divlist:
            del div['SCHED_TYPE']
        config_status = liststatus_tuple.config_status
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    def readDBraw(self):
        liststatus_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = liststatus_tuple.list
        config_status = liststatus_tuple.config_status
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    def readSchedDB(self, age, gender):
        dbgame_list = self.dbinterface.findElimTournDivisionSchedule(age, gender, min_game_id=3)
        game_list = []
        for dbgame in dbgame_list:
            print dbgame
            game_list.append({'gameday_id':dbgame[gameday_id_CONST],
                             'start_time':dbgame[start_time_CONST]})
        return dbgame_list

    def updateDBDivFields(self, divinfo):
        # ref http://stackoverflow.com/questions/5646798/mongodb-updating-subdocument
        # for updating subdocument
        div_id = divinfo['div_id']
        divfield_list = divinfo['divfield_list']
        query_obj = {"DIV_ID":div_id}
        operator_obj = {"DIVFIELD_LIST":divfield_list}
        self.dbinterface.updatedoc(query_obj, "$set", operator_obj)

