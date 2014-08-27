#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
import logging
age_CONST = 'AGE'
gen_CONST = 'GEN'
div_id_CONST = 'DIV_ID'
totalteams_CONST = 'TOTALTEAMS'
totalbrackets_CONST = 'TOTALBRACKETS'
elimination_num_CONST = 'ELIMINATION_NUM'
elimination_type_CONST = 'ELIMINATION_TYPE'
field_id_list_CONST = 'FIELD_ID_LIST'
gameinterval_CONST = 'GAMEINTERVAL'
rr_gamedays_CONST = 'RR_GAMEDAYS'
gameday_id_CONST = 'GAMEDAY_ID'
start_time_CONST = 'START_TIME'
gameday_data_CONST = 'GAMEDAY_DATA'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')
_List_Status_Mode = namedtuple('_List_Status_Mode',
    'list config_status oddnum_mode')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface(object):
    def __init__(self, mongoClient, userid_name, newcol_name):
        self.dbinterface = MongoDBInterface(mongoClient, userid_name, newcol_name, db_col_type=DB_Col_Type.ElimTourn)

    def writeDB(self, divinfo_str, config_status):
        divinfo_list = json.loads(divinfo_str)
        for divinfo in divinfo_list:
            # convert field_id_str field into list of int elements
            divinfo['field_id_list'] = [int(x) for x in divinfo['field_id_str'].split(',')]
            del divinfo['field_id_str']  # remove old element
        # convert keys to uppercase
        document_list = [{k.upper():v for k,v in x.items()} for x in divinfo_list]
        set_obj = {'CONFIG_STATUS':config_status, 'ODDNUM_MODE':oddnum_mode}
        self.dbinterface.updateInfoDocument(document_list, set_obj, 'DIV_ID')

    def readDB(self):
        liststatus_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = liststatus_tuple.list
        result = listresult_tuple.result
        config_status = result['CONFIG_STATUS']
        # update field_id list val as string of comma-separated field_id's
        for div in divlist:
            div[field_id_list_CONST] = ','.join(str(f)
                                           for f in divinfo[field_id_list_CONST])
            del div['SCHED_TYPE']
            del div['USER_ID']
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    # read from DB, and convert fieldnames to lower case, but don't convert lists
    # back to string representation
    def readDBraw(self):
        liststatus_tuple = self.dbinterface.getInfoDocument('DIV_ID')
        divlist = liststatus_tuple.list
        result = listresult_tuple.result
        config_status = result['CONFIG_STATUS']
        oddnum_mode = result['ODDNUM_MODE']
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

    def drop_collection(self):
        self.dbinterface.drop_collection()

