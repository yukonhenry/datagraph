#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface
USERID_NAME = 'USERID_NAME'
USERID_LIST = 'USERID_LIST'
class UserDBInterface(BaseDBInterface):
    def __init__(self, mongoClient):
        BaseDBInterface.__init__(self, mongoClient, 'yukonadmin',
            USERID_LIST, DB_Col_Type.UserInfo, 'USER_ID')

    def check_user(self, userid_name):
        query_obj = {USERID_NAME:{"$exists":True}}
        doc_list = self.dbinterface.getDocuments(query_obj)
        if doc_list:
            result = 1 if userid_name in [x[USERID_NAME] for x in doc_list] else 0
        else:
            result = 0
        return result

    def writeDB(self, userid_name):
        '''create dummy entry with config_status - just to make it compatible with
        dbInterface.getScheduleCollection
        '''
        document = {USERID_NAME:userid_name}
        self.dbinterface.insertdoc(document)
