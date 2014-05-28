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
        self.dbinterface = MongoDBInterface(mongoClient, collection_name=newcol_name, db_col_type=DB_Col_Type.PreferenceInfo)
