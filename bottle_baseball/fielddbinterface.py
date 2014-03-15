#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
from dateutil import parser
from datetime import date
import logging

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')

field_id_CONST = 'FIELD_ID'
field_name_CONST = 'FIELD_NAME'
primaryuse_list_CONST = 'PRIMARYUSE_LIST'
start_date_CONST = 'START_DATE'
end_date_CONST = 'END_DATE'
start_time_CONST = 'START_TIME'
end_time_CONST = 'END_TIME'
dayweek_list_CONST = 'DAYWEEK_LIST'
numgamedays_CONST = 'NUMGAMEDAYS'

class FieldDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbInterface = MongoDBInterface(mongoClient, newcol_name,
                                            db_col_type=DB_Col_Type.FieldInfo)

    def writeDB(self, fieldinfo_str, config_status, divstr_colname, divstr_db_type):
        fieldinfo_list = json.loads(fieldinfo_str)
        for fieldinfo in fieldinfo_list:
            start_date_str = fieldinfo['start_date']
            end_date_str = fieldinfo['end_date']
            dayweek_list = fieldinfo['dayweek_str'].split(',')
            if len(dayweek_list) == 1 and not dayweek_list[0]:
                numgamedays = 0
            else:
                numgamedays = self.calcNumGameDays(start_date_str, end_date_str,
                                                   dayweek_list)
            fieldinfo['numgamedays'] = numgamedays
            fieldinfo['dayweek_list'] = dayweek_list
            # check if primary use is not empty
            fieldinfo['primaryuse_list'] = fieldinfo['primaryuse_str'].split(',')
            del fieldinfo['dayweek_str']
            del fieldinfo['primaryuse_str']
        document_list = [{k.upper():v for k,v in x.items()} for x in fieldinfo_list]
        self.dbInterface.updateFieldInfoDocument(document_list, config_status, divstr_colname=divstr_colname, divstr_db_type=divstr_db_type)

    def readDB(self):
        liststatus_tuple = self.dbInterface.getInfoDocument()
        field_list = liststatus_tuple.list
        config_status = liststatus_tuple.config_status
        for field in field_list:
            field['primaryuse_str'] = ','.join(str(f) for f in field[primaryuse_list_CONST])
            del field[primaryuse_list_CONST]
            field['dayweek_str'] = ','.join(str(f) for f in field[dayweek_list_CONST])
            del field[dayweek_list_CONST]
        fieldinfo_list = [{k.lower():v for k,v in x.items()} for x in field_list]
        return _List_Status(fieldinfo_list, config_status)
        '''
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
                                 'dayweek_str':','.join(str(f) for f in fieldinfo[dayweek_list_CONST]),
                                 'numgamedays':fieldinfo[numgamedays_CONST]})
        f_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldinfo_list)).get(x)
        return _List_Indexer(fieldinfo_list, f_indexerGet)
    '''

    def updateFieldTimes(self, fieldtime_str):
        fieldtime_dict = json.loads(fieldtime_str)
        for fieldtime in fieldtime_dict:
            print 'fieldtime', fieldtime
            field_id = fieldtime['field_id']

    def calcNumGameDays(self, start_date_str, end_date_str, dayweek_list):
        start_date = parser.parse(start_date_str)
        # get integer day of week number
        start_day = start_date.weekday()
        end_date = parser.parse(end_date_str)
        end_day = end_date.weekday()
        # create list of available dates during last week
        # calc # days between start and end dates
        diff_days = (end_date - start_date).days
        diff_fullweeks = diff_days / 7
        # calc baseline number of game days based on full weeks
        numgamedays = len(dayweek_list)*diff_fullweeks
        # available days in the last week
        avail_days = diff_days % diff_fullweeks
        if avail_days > 0:
            if end_day >= start_day:
                lw_list = range(start_day, end_day+1)
            else:
                # days of week are numbered as a circular list so take care
                # of case where start day is later than end day wrt day num
                # i.e. start = Fri and end = Mon
                lw_list = range(start_day, 7) + range(end_day+1)
            # calculate number of game days during last (partial) week
            # by taking intersection of available days during last week
            # and weekly game days
            numgamedays += len(set(lw_list).intersection(dayweek_list))
        return numgamedays
