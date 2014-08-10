#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface

class UserDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, newcol_name,
            DB_Col_Type.UserInfo, 'USER_ID')
