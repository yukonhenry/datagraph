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
match_id_CONST = 'MATCH_ID'
start_time_CONST = 'START_TIME'
gameday_data_CONST = 'GAMEDAY_DATA'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')
''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, db_col_type=DB_Col_Type.ElimTourn)

    def writeDB(self, divinfo_str, config_status):
        divinfo_list = json.loads(divinfo_str)
        for divinfo in divinfo_list:
            # convert field_id_str field into list of int elements
            divinfo['field_id_list'] = [int(x) for x in divinfo['field_id_str'].split(',')]
            del divinfo['field_id_str']  # remove old element
        # convert keys to uppercase
        document_list = [{k.upper():v for k,v in x.items()} for x in divinfo_list]
        self.dbInterface.updateInfoDocument(document_list, config_status)

    def readDB(self):
        liststatus_tuple = self.dbInterface.getInfoDocument()
        divlist = liststatus_tuple.list
        config_status = liststatus_tuple.config_status
        # update field_id list val as string of comma-separated field_id's
        for div in divlist:
            div[field_id_list_CONST] = ','.join(str(f)
                                           for f in divinfo[field_id_list_CONST])
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    # read from DB, and convert fieldnames to lower case, but don't convert lists
    # back to string representation
    def readDBraw(self):
        liststatus_tuple = self.dbInterface.getInfoDocument()
        divlist = liststatus_tuple.list
        config_status = liststatus_tuple.config_status
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    def readSchedDB(self, age, gender):
        dbgame_list = self.dbInterface.findElimTournDivisionSchedule(age, gender, min_game_id=3)
        game_list = []
        for dbgame in dbgame_list:
            print dbgame
            game_list.append({'gameday_id':dbgame[gameday_id_CONST],
                             'start_time':dbgame[start_time_CONST]})
        return dbgame_list

