#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface
import simplejson as json
from collections import namedtuple
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
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, rr_type_flag=False)

    def writeDB(self, divinfo_str):
        divinfo_dict = json.loads(divinfo_str)
        for division in divinfo_dict:
            div_id = division['div_id']
            document = {div_id_CONST:int(div_id), age_CONST:division['div_age'],
                        gen_CONST:division['div_gen'],
                        totalteams_CONST:int(division['totalteams']),
                        totalbrackets_CONST: int(division['totalbrackets']),
                        elimination_num_CONST:int(division['elimination_num']),
                        elimination_type_CONST:division['elimination_type'],
                        field_id_list_CONST:division['field_id_str'].split(),
                        gameinterval_CONST:int(division['gameinterval']),
                        rr_gamedays_CONST:int(division['rr_gamedays'])}
            self.dbInterface.updateTournamentDivInfo(document, div_id)

    def readDB(self):
        dvlist = self.dbInterface.getTournamentDivInfo().dict_list
        divinfo_list = []
        for divinfo in dvlist:
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

