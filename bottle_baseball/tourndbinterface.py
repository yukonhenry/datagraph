#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface
import simplejson as json
age_CONST = 'AGE'
gen_CONST = 'GEN'
div_id_CONST = 'DIV_ID'
totalteams_CONST = 'TOTALTEAMS'
totalbrackets_CONST = 'TOTALBRACKETS'
elimination_num_CONST = 'ELIMINATION_NUM'
field_id_list_CONST = 'FIELD_ID_LIST'
sched_type_CONST = 'SCHED_TYPE'

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, rr_type_flag=False)

    def writeDB(divinfo_str):
        divinfo_dict = json.loads(divinfo_str)
        for division in divinfo_dict:
            self.dbInterface.updateTournamentDivInfo(div_id=division['div_id'],
                                                     age=division['div_age'],
                                                     gen=division['div_gen'],
                                                     totalteams=division['totalteams'],
                                                     totalbrackets=division['totalbrackets'],
                                                     elimination_num=division['elimination_num'],
                                                     field_id_list=division['field_id_str'].split())

    def readDB():
        dvlist = self.dbInterface.getTournamentDivInfo()
        divinfo_list = []
        for divinfo in dvlist:
            divinfo_list.append({'div_id':divinfo[div_id_CONST],
                                 'div_age':divinfo[age_CONST],
                                 'div_gen':divinfo[gen_CONST],
                                 'totalteams':divinfo[totalteams_CONST],
                                 'totalbrackets':divinfo[totalbrackets_CONST],
                                 'elimination_num':divinfo[elimination_num_CONST],
                                 'field_id_str':str(divinfo[field_id_list])})
        return divinfo_list
