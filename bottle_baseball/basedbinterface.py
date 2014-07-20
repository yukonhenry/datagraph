#!/usr/bin/python
''' Copyright YukonTR 2014 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
from dateutil import parser

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')
_PlusList_Status = namedtuple('_PlusList_Status', 'list config_status divstr_colname divstr_db_type')

class BaseDBInterface:
    def __init__(self, mongoClient, newcol_name, db_col_type, capid_str):
        self.dbinterface = MongoDBInterface(mongoClient, newcol_name,
            db_col_type)
        # capid_str is the idprop, but named to remember that it is upper case
        self.capid_str = capid_str

    def writeDB(self, info_str, config_status, divstr_colname, divstr_db_type):
        info_list = json.loads(info_str)
        document_list = [{k.upper():v for k,v in x.items()} for x in info_list]
        self.dbinterface.updateInfoPlusDocument(document_list, config_status,
            divstr_colname=divstr_colname, divstr_db_type=divstr_db_type,
            id_str=self.capid_str)

    def write_constraint_status(self, cstatus_list):
        operator = "$set"
        for cstatus in cstatus_list:
            query_obj = {'PREF_ID':cstatus['pref_id']}
            operator_obj = {'SATISFY':cstatus['status']}
            self.dbinterface.updatedoc(query_obj, operator, operator_obj)

    def readDB(self):
        # readDB is for returning to client UI
        liststatus_qtuple = self.dbinterface.getInfoPlusDocument(self.capid_str)
        rawlist = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        for raw in rawlist:
            del raw['SCHED_TYPE']
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        info_list = [{k.lower():v for k,v in x.items()} for x in rawlist]
        return _PlusList_Status(info_list, config_status, divstr_colname,
            divstr_db_type)

    def readDBraw(self):
        # readDBraw if for db reads from within py code
        liststatus_qtuple = self.dbinterface.getInfoPlusDocument(self.capid_str)
        rawlist = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        info_list = [{k.lower():v for k,v in x.items()} for x in rawlist]
        return _PlusList_Status(info_list, config_status, divstr_colname,
            divstr_db_type)

    def drop_collection(self):
        self.dbinterface.drop_collection()
