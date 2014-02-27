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

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, db_col_type=DB_Col_Type.ElimTourn)

    def writeDB(self, divinfo_str, configdone_flag):
        divinfo_dict = json.loads(divinfo_str)
        document_list = []
        for divinfo in divinfo_dict:
            document_list.append({div_id_CONST:int(divinfo['div_id']),
                                 age_CONST:divinfo['div_age'],
                                 gen_CONST:divinfo['div_gen'],
                                 totalteams_CONST:int(divinfo['totalteams']),
                                 totalbrackets_CONST: int(divinfo['totalbrackets']),
                                 elimination_num_CONST:int(divinfo['elimination_num']),
                                 elimination_type_CONST:divinfo['elimination_type'],
                                 field_id_list_CONST:divinfo['field_id_str'].split(),
                                 gameinterval_CONST:int(divinfo['gameinterval']),
                                 rr_gamedays_CONST:int(divinfo['rr_gamedays'])})
        self.dbInterface.updateDivInfoDocument(document_list, configdone_flag)

    def readDB(self):
        divlist = self.dbInterface.getDivInfoDocument().dict_list
        divinfo_list = []
        for divinfo in divlist:
            divinfo_list.append({'div_id':divinfo[div_id_CONST],
                                 'div_age':divinfo[age_CONST],
                                 'div_gen':divinfo[gen_CONST],
                                 'totalteams':divinfo[totalteams_CONST],
                                 'totalbrackets':divinfo[totalbrackets_CONST],
                                 'elimination_num':divinfo[elimination_num_CONST],
                                 'elimination_type':divinfo[elimination_type_CONST],
                                 'field_id_str':','.join(str(f) for f in divinfo[field_id_list_CONST]),
                                 'gameinterval':divinfo[gameinterval_CONST],
                                 'rr_gamedays':divinfo[rr_gamedays_CONST]})
        d_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(divinfo_list)).get(x)
        return _List_Indexer(divinfo_list, d_indexerGet)

    def readSchedDB(self, age, gender):
        dbgame_list = self.dbInterface.findElimTournDivisionSchedule(age, gender, min_game_id=3)
        game_list = []
        for dbgame in dbgame_list:
            print dbgame
            game_list.append({'gameday_id':dbgame[gameday_id_CONST],
                             'start_time':dbgame[start_time_CONST]})
        return dbgame_list

