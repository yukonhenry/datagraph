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
_List_Status_Mode = namedtuple('_List_Status_Mode',
    'list config_status oddnum_mode')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class RRDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, userid_name, newcol_name,
            DB_Col_Type.RoundRobin, 'DIV_ID')

    def writeDB(self, divinfo_str, config_status, oddnum_mode):
        divinfo_list = json.loads(divinfo_str)
        document_list = [{k.upper():v for k,v in x.items()} for x in divinfo_list]
        set_obj = {'CONFIG_STATUS':config_status, 'ODDNUM_MODE':oddnum_mode}
        self.dbinterface.updateInfoDocument(document_list, set_obj, 'DIV_ID')

    def updateDB(self, update_data_str):
        # right now this update operation is hardcoded to update divfield_list
        update_data_list = json.loads(update_data_str)
        for update_obj in update_data_list:
            query_obj = {'DIV_ID':update_obj['div_id']}
            # field collection name is an item assocated with divfield list -
            # provides reference col name if dereference field_id is required
            operator_obj = {"DIVFIELD_LIST":update_obj['divfield_list'],
                "FIELDCOL_NAME":update_obj['fieldcol_name']}
            self.dbinterface.updatedoc(query_obj, "$set", operator_obj)

    def readDB(self):
        listresult_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = listresult_tuple.list
        for div in divlist:
            del div['SCHED_TYPE']
            del div['USER_ID']
        result = listresult_tuple.result
        config_status = result['CONFIG_STATUS']
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    def readDBraw(self):
        listresult_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = listresult_tuple.list
        result = listresult_tuple.result
        config_status = result['CONFIG_STATUS']
        oddnum_mode = result['ODDNUM_MODE']
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status_Mode(divinfo_list, config_status, oddnum_mode)

    def readSchedDB(self, age, gender):
        dbgame_list = self.dbinterface.findElimTournDivisionSchedule(age, gender, min_game_id=3)
        game_list = []
        for dbgame in dbgame_list:
            print dbgame
            game_list.append({'gameday_id':dbgame[gameday_id_CONST],
                             'start_time':dbgame[start_time_CONST]})
        return dbgame_list
