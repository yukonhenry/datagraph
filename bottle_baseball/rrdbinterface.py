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
numweeks_CONST = 'NUMWEEKS'
numgdaysperweek_CONST = 'NUMGDAYSPERWEEK'
totalgamedays_CONST = 'TOTALGAMEDAYS'
gameinterval_CONST = 'GAMEINTERVAL'
division_list_CONST = 'DIVISION_LIST'
gameday_id_CONST = 'GAMEDAY_ID'
match_id_CONST = 'MATCH_ID'
start_time_CONST = 'START_TIME'
gameday_data_CONST = 'GAMEDAY_DATA'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class RRDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, collection_name=newcol_name, db_col_type=DB_Col_Type.RoundRobin)

    def writeDB(self, divinfo_str):
        divinfo_dict = json.loads(divinfo_str)
        document_list = []
        for divinfo in divinfo_dict:
            document_list.append({div_id_CONST:int(divinfo['div_id']),
                                 age_CONST:divinfo['div_age'],
                                 gen_CONST:divinfo['div_gen'],
                                 totalteams_CONST:int(divinfo['totalteams']),
                                 numweeks_CONST:int(divinfo['numweeks']),
                                 numgdaysperweek_CONST:int(divinfo['numgdaysperweek']),
                                 totalgamedays_CONST:int(divinfo['totalgamedays']),
                                 gameinterval_CONST:int(divinfo['gameinterval'])})
        self.dbInterface.updateDivInfoDocument({division_list_CONST:document_list})

    def readDB(self):
        divlist = self.dbInterface.getDivInfoDocument().dict_list
        divinfo_list = []
        for divinfo in divlist:
            divinfo_list.append({'div_id':divinfo[div_id_CONST],
                                 'div_age':divinfo[age_CONST],
                                 'div_gen':divinfo[gen_CONST],
                                 'totalteams':divinfo[totalteams_CONST],
                                 'numweeks':divinfo[numweeks_CONST],
                                 'numgdaysperweek':divinfo[numgdaysperweek_CONST],
                                 'totalgamedays':divinfo[totalgamedays_CONST],
                                 'gameinterval':divinfo[gameinterval_CONST]})
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

