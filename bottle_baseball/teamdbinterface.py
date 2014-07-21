#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface

class TeamDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, newcol_name,
            DB_Col_Type.TeamInfo, 'DT_ID')

    def check_docexists(self):
        # use DT_ID key to see if any teaminfo doc exists
        return self.dbinterface.check_docexists("DT_ID")
