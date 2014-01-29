#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
import logging

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')

field_id_CONST = 'FIELD_ID'
field_name_CONST = 'FIELD_NAME'
primaryuse_list_CONST = 'PRIMARYUSE_LIST'
start_date_CONST = 'START_DATE'
end_date_CONST = 'END_DATE'
start_time_CONST = 'START_TIME'
end_time_CONST = 'END_TIME'
dayweek_CONST = 'DAYWEEK'

class FieldDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name,
                                            db_col_type=DB_Col_Type.FieldInfo)

    def writeDB(self, fieldinfo_str):
        fieldinfo_dict = json.loads(fieldinfo_str)
        for fieldinfo in fieldinfo_dict:
            field_id = fieldinfo['field_id']
            document = {field_id_CONST:int(field_id),
                        field_name_CONST:fieldinfo['field_name'],
                        primaryuse_list_CONST:fieldinfo['primaryuse_str'].split(','),
                        start_date_CONST:fieldinfo['start_date'],
                        end_date_CONST:fieldinfo['end_date'],
                        start_time_CONST:fieldinfo['start_time'],
                        end_time_CONST:fieldinfo['end_time'],
                        dayweek_CONST:fieldinfo['dayweek'].split(',')}
            self.dbInterface.updateFieldInfo(document, field_id)

    def readDB(self):
        flist = self.dbInterface.getFieldInfo().dict_list
        fieldinfo_list = []
        for fieldinfo in flist:
            fieldinfo_list.append({'field_id':fieldinfo[field_id_CONST],
                                 'field_name':fieldinfo[field_name_CONST],
                                 'primaryuse_str':','.join(str(f) for f in fieldinfo[primaryuse_list_CONST]),
                                 'start_date':fieldinfo[start_date_CONST],
                                 'end_date':fieldinfo[end_date_CONST],
                                 'start_time':fieldinfo[start_time_CONST],
                                 'end_time':fieldinfo[end_time_CONST],
                                 'dayweek_str':','.join(str(f) for f in fieldinfo[dayweek_CONST])})
        f_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldinfo_list)).get(x)
        return _List_Indexer(fieldinfo_list, f_indexerGet)

    def updateFieldTimes(self, fieldtime_str):
        fieldtime_dict = json.loads(fieldtime_str)
        for fieldtime in fieldtime_dict:
            print 'fieldtime', fieldtime
            field_id = fieldtime['field_id']

