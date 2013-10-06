#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface
import simplejson as json

class NewSchedule:
    def __init__(self, mongoClient, newcol_name, divinfo_str):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name, rr_type=False)
        self.divinfo_dict = json.loads(divinfo_str)
        for division in self.divinfo_dict:
            self.dbInterface.updateDivInfo(div_id=division['div_id'],
                                           age=division['div_age'], gen=division['div_gen'],
                                           totalteams=division['totalteams'],
                                           totalbrackets=division['totalbrackets'])
            