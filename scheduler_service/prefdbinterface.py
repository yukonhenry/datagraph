#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface

class PrefDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, userid_name, newcol_name,
            DB_Col_Type.PreferenceInfo, 'PREF_ID')

    def write_constraint_status(self, cstatus_list):
        operator = "$set"
        for cstatus in cstatus_list:
            query_obj = {'PREF_ID':cstatus['pref_id']}
            operator_obj = {'SATISFY':cstatus['status']}
            self.dbinterface.updatedoc(query_obj, operator, operator_obj)
