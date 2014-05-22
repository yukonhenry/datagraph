#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
from schedule_util import convertJStoPY_daylist, convertPYtoJS_daylist, \
    getcalendarmap_list
import simplejson as json
from collections import namedtuple
from dateutil import parser
from sched_exceptions import SchedulerConfigurationError
import logging

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')
_FieldList_Status = namedtuple('_FieldList_Status', 'list config_status divstr_colname divstr_db_type')

field_id_CONST = 'FIELD_ID'
field_name_CONST = 'FIELD_NAME'
primaryuse_list_CONST = 'PRIMARYUSE_LIST'
start_date_CONST = 'START_DATE'
end_date_CONST = 'END_DATE'
start_time_CONST = 'START_TIME'
dayweek_list_CONST = 'DAYWEEK_LIST'
totalfielddays_CONST = 'TOTALFIELDDAYS'
date_format_CONST = "%m/%d/%Y"
class FieldDBInterface:
    def __init__(self, mongoClient, newcol_name):
        self.dbinterface = MongoDBInterface(mongoClient,
            newcol_name, db_col_type=DB_Col_Type.FieldInfo)

    def writeDB(self, fieldinfo_str, config_status, divstr_colname, divstr_db_type):
        fieldinfo_list = json.loads(fieldinfo_str)
        for fieldinfo in fieldinfo_list:
            if fieldinfo['dayweek_str']:
                temp_list = [int(x) for x in fieldinfo['dayweek_str'].split(',')]
                fieldinfo['dayweek_list'] = convertJStoPY_daylist(temp_list)
            else:
                fieldinfo['dayweek_list'] = []
            # check if primary use is not empty
            if fieldinfo['primaryuse_str']:
                fieldinfo['primaryuse_list'] = [int(x)
                    for x in fieldinfo['primaryuse_str'].split(',')]
            else:
                fieldinfo['primaryuse_list'] = []
            fieldinfo['calendarmap_list'] = getcalendarmap_list(fieldinfo['dayweek_list'],
                fieldinfo['start_date'], fieldinfo['totalfielddays'])
            del fieldinfo['dayweek_str']
            del fieldinfo['primaryuse_str']
        document_list = [{k.upper():v for k,v in x.items()} for x in fieldinfo_list]
        self.dbinterface.updateFieldInfoDocument(document_list, config_status, divstr_colname=divstr_colname, divstr_db_type=divstr_db_type)

    def readDB(self):
        liststatus_qtuple = self.dbinterface.getFieldInfoDocument()
        field_list = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        for field in field_list:
            field['primaryuse_str'] = ','.join(str(f) for f in field[primaryuse_list_CONST])
            del field[primaryuse_list_CONST]
            temp_list = convertPYtoJS_daylist(field[dayweek_list_CONST])
            field['dayweek_str'] = ','.join(str(f) for f in temp_list)
            del field[dayweek_list_CONST]
            field['calendarmap_list'] = [{'fieldday_id':x['fieldday_id'],
                'date':x['date'].strftime(date_format_CONST)} for x in field['CALENDARMAP_LIST']]
            del field['CALENDARMAP_LIST']
            # http://stackoverflow.com/questions/15411107/delete-a-dictionary-item-if-the-key-exists (None is the return value if closed_list doesnt exist
        fieldinfo_list = [{k.lower():v for k,v in x.items()} for x in field_list]
        return _FieldList_Status(fieldinfo_list, config_status, divstr_colname,
                                 divstr_db_type)

    # read from DB, but don't covert lists back into string representation
    # also don't covert the dayweek_list elements back to JS format
    def readDBraw(self):
        liststatus_qtuple = self.dbinterface.getFieldInfoDocument()
        field_list = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        fieldinfo_list = [{k.lower():v for k,v in x.items()} for x in field_list]
        return _FieldList_Status(fieldinfo_list, config_status, divstr_colname,
                                 divstr_db_type)

    def updateFieldTimes(self, fieldtime_str):
        fieldtime_dict = json.loads(fieldtime_str)
        for fieldtime in fieldtime_dict:
            print 'fieldtime', fieldtime
            field_id = fieldtime['field_id']

    def calc_totalfielddays(self, start_date_str, end_date_str, dayweek_list):
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
        totalfielddays = len(dayweek_list)*diff_fullweeks
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
            totalfielddays += len(set(lw_list).intersection(dayweek_list))
        return totalfielddays

    def adjust_config(self, action_type, field_id, delta_list):
        query_obj = {"FIELD_ID":field_id}
        if action_type == 'remove':
            # first decrease totalfielddays field
            # db.<collection>.update({FIELD_ID:field_id},
            #   {$inc:{TOTALFIELDDAYS:-length(delta_list)}})
            operator = "$inc"
            operator_obj = {"TOTALFIELDDAYS":-len(delta_list)}
            status = self.dbinterface.updatedoc(query_obj, operator,
                operator_obj)
            # next remove entry from calendar map_list
            # ref http://stackoverflow.com/questions/6928354/mongodb-remove-subdocument-from-document
            # db.PHMSA.update({"FIELD_ID":1},{$pull:{CALENDARMAP_LIST:{"fieldday_id":2}}})
            operator = "$pull"
            for fieldday_id in delta_list:
                self.dbinterface.updatedoc(query_obj, operator,
                    {"CALENDARMAP_LIST":{"fieldday_id":fieldday_id}})
            # next decrement all the fieldday_id fields after the entry above
            # was removed so that fieldday_id's are still contiguous
            field_curs = self.dbinterface.getdoc(query_obj)
            if field_curs.count() > 1:
                # pymongo cursor doc at
                # http://api.mongodb.org/python/current/api/pymongo/cursor.html
                raise SchedulerConfigurationError("fielddbinterface:adjust_config: Query returns more than one document for field_id %d" % (field_id,))
            else:
                totalfielddays = field_curs[0]['TOTALFIELDDAYS']
                # reassign fieldday_id values in calendarmap_list
                operator = "$set"
                for fieldday_id in range(1, totalfielddays+1):
                    index = fieldday_id-1
                    operator_key = "CALENDARMAP_LIST."+str(index)+".fieldday_id"
                    operator_obj = {operator_key:fieldday_id}
                    self.dbinterface.updatedoc(query_obj, operator, operator_obj)
            # add closed list field - this is for informational purposes only for the UI that can be displayed to the user. CLOSED_LIST has already been
            # processed on the UI side.
            operator = "$set"
            operator_obj = {'CLOSED_LIST':delta_list}
            self.dbinterface.updatedoc(query_obj, operator, operator_obj,
                upsert_flag=True)

    def findcommon_dates(self, field_list, fieldinfo_list,
        fieldinfo_indexerGet):
        ''' Find common dates from multiple calendarmap_lists and return the
        common dates, along with the fieldday_id's corresponding to each
        list '''
        # first create list of tuples, with x[0] field_id, x[1] calendarmap_list
        maptuple_list = [(f,fieldinfo_list[fieldinfo_indexerGet(f)]['calendarmap_list']) for f in field_list]
        # use set comprehension as described in
        # https://docs.python.org/2/tutorial/datastructures.html#sets
        dateset_list = [{y['date'] for y in x[1]} for x in maptuple_list]
        commondate_list = list(set.intersection(*dataset_list))
        commonmap_list = []
        commonmap_list = [(x['fieldday_id'], y['fieldday_id'])
            for x in map1_list for y in map2_list
            if x['date'] in commondate_list and y['date'] in commondate_list]
        return commonmap_list

    def drop_collection(self):
        self.dbinterface.drop_collection()
