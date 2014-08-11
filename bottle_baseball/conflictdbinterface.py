#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface

class ConflictDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, userid_name, newcol_name,
            DB_Col_Type.ConflictInfo, 'CONFLICT_ID')

    def addconflict_prefcount(self, conflict_id, count):
        operator = "$set"
        query_obj = {'CONFLICT_ID':conflict_id}
        operator_obj = {'CONFLICT_NUM':count}
        self.dbinterface.updatedoc(query_obj, operator, operator_obj)

    def write_conflict_status(self, cstatus_list):
        operator = "$set"
        for cstatus in cstatus_list:
            query_obj = {'CONFLICT_ID':cstatus['conflict_id']}
            operator_obj = {'CONFLICT_AVOID':cstatus['count']}
            self.dbinterface.updatedoc(query_obj, operator, operator_obj)

