#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
import logging

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')

field_id_CONST = 'FIELD_ID'
field_name_CONST = 'FIELD_NAME'
primaryuse_list_CONST = 'PRIMARYUSE_LIST'
start_time_CONST = 'START_TIME'
end_time_CONST = 'END_TIME'

class FieldDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, db_col_type=DB_Col_Type.FieldInfo)

    def writeDB(self, fieldinfo_str):
        fieldinfo_dict = json.loads(fieldinfo_str)
        for fieldinfo in fieldinfo_dict:
            field_id = fieldinfo['field_id']
            document = {field_id_CONST:int(field_id),
                        field_name_CONST:fieldinfo['field_name'],
                        primaryuse_list_CONST:fieldinfo['primaryuse'].split(),
                        start_time_CONST:fieldinfo['start_time'],
                        end_time_CONST:fieldinfo['end_time'])}
            self.dbInterface.updateFieldInfo(document, field_id)

    def readDB(self):
        divlist = self.dbInterface.getTournamentDivInfo().dict_list
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

