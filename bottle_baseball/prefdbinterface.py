#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
from dateutil import parser

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')

class PrefDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbinterface = MongoDBInterface(mongoClient,
            collection_name=newcol_name, db_col_type=DB_Col_Type.PreferenceInfo)

    def writeDB(self, info_str, config_status):
        info_list = json.loads(info_str)
        document_list = [{k.upper():v for k,v in x.items()} for x in info_list]
        self.dbinterface.updateInfoDocument(document_list, config_status, 'PREF_ID')

    def readDB(self):
        # readDB is for returning to client UI
        liststatus_tuple = self.dbinterface.getInfoDocument('PREF_ID')
        rawlist = liststatus_tuple.list
        for raw in rawlist:
            del raw['SCHED_STATUS']
        config_status = liststatus_tuple.config_status
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        info_list = [{k.lower():v for k,v in x.items()} for x in rawlist]
        return _List_Status(info_list, config_status)

    def readDBraw(self):
        # readDBraw if for db reads from within py code
        liststatus_tuple = self.dbinterface.getInfoDocument('PREF_ID')
        rawlist = liststatus_tuple.list
        config_status = liststatus_tuple.config_status
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        info_list = [{k.lower():v for k,v in x.items()} for x in rawlist]
        return _List_Status(info_list, config_status)
