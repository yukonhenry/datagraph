#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface

class TeamDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name, sched_cat):
        BaseDBInterface.__init__(self, mongoClient, userid_name,
            newcol_name, sched_cat,
            DB_Col_Type.TeamInfo, 'DT_ID')

    def check_docexists(self):
        # use DT_ID key to see if any teaminfo doc exists
        return self.dbinterface.check_docexists("DT_ID")
