#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface
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
_PlusList_Status = namedtuple('_PlusList_Status', 'list config_status divstr_colname divstr_db_type')

field_id_CONST = 'FIELD_ID'
field_name_CONST = 'FIELD_NAME'
primaryuse_list_CONST = 'PRIMARYUSE_LIST'
start_date_CONST = 'START_DATE'
end_date_CONST = 'END_DATE'
start_time_CONST = 'START_TIME'
dayweek_list_CONST = 'DAYWEEK_LIST'
TFD = 'TFD'
date_format_CONST = "%m/%d/%Y"
''' some acronyms used:
pr - primaryuse_str
dr - dayweek_str
tfd - tofalfielddays
'''
class FieldDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, userid_name, newcol_name,
            DB_Col_Type.FieldInfo, 'FIELD_ID')

    def writeDB(self, fieldinfo_str, config_status, divstr_colname, divstr_db_type):
        fieldinfo_list = json.loads(fieldinfo_str)
        for fieldinfo in fieldinfo_list:
            if fieldinfo['dr']:
                temp_list = [int(x) for x in fieldinfo['dr'].split(',')]
                fieldinfo['dayweek_list'] = convertJStoPY_daylist(temp_list)
            else:
                fieldinfo['dayweek_list'] = []
            # check if primary use is not empty
            if fieldinfo['pr']:
                fieldinfo['primaryuse_list'] = [int(x)
                    for x in fieldinfo['pr'].split(',')]
            else:
                fieldinfo['primaryuse_list'] = []
            fieldinfo['calendarmap_list'] = getcalendarmap_list(fieldinfo['dayweek_list'],
                fieldinfo['start_date'], fieldinfo['tfd'])
            del fieldinfo['dr']
            del fieldinfo['pr']
        document_list = [{k.upper():v for k,v in x.items()} for x in fieldinfo_list]
        self.dbinterface.updateInfoPlusDocument(document_list, config_status,
            divstr_colname=divstr_colname, divstr_db_type=divstr_db_type,
            id_str='FIELD_ID')

    def readDB(self):
        liststatus_qtuple = self.dbinterface.getInfoPlusDocument('FIELD_ID')
        field_list = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        for field in field_list:
            del field['SCHED_TYPE']
            del field['USER_ID']
            field['pr'] = ','.join(str(f) for f in field[primaryuse_list_CONST])
            del field[primaryuse_list_CONST]
            temp_list = convertPYtoJS_daylist(field[dayweek_list_CONST])
            field['dr'] = ','.join(str(f) for f in temp_list)
            del field[dayweek_list_CONST]
            # convert date into string format
            for cmap in field['CALENDARMAP_LIST']:
                cmap['date'] = cmap['date'].strftime(date_format_CONST)
            # if there are any time changes for a particular calendar date, add the
            # date to the timechange_list.  Check for only start_time as start_time and end_time will both be present.
            # creating the timechange_list item for the benefit of sending back to client
            timechange_list = [x['date'] for x in field['CALENDARMAP_LIST'] if 'start_time' in x]
            if timechange_list:
                field['timechange_list'] = timechange_list
            if 'CLOSED_LIST' in field:
                field['closed_list'] = [x.strftime(date_format_CONST) for x in field['CLOSED_LIST']]
                del field['CLOSED_LIST']
            # http://stackoverflow.com/questions/15411107/delete-a-dictionary-item-if-the-key-exists (None is the return value if closed_list doesnt exist
        fieldinfo_list = [{k.lower():v for k,v in x.items()} for x in field_list]
        return _PlusList_Status(fieldinfo_list, config_status, divstr_colname,
                                 divstr_db_type)

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
        if action_type == 'remove':
            query_obj = {"FIELD_ID":field_id}
            # first decrease totalfielddays field
            # db.<collection>.update({FIELD_ID:field_id},
            #   {$inc:{TOTALFIELDDAYS:-length(delta_list)}})
            operator = "$inc"
            operator_obj = {'TFD':-len(delta_list)}
            status = self.dbinterface.updatedoc(query_obj, operator,
                operator_obj)
            # get dates before pulling the entries corresponding to the removed fields:
            projection_obj = {"CALENDARMAP_LIST.$":1, '_id':0}
            closed_list = []
            for fieldday_id in delta_list:
                datequery_obj = {"FIELD_ID":field_id, "CALENDARMAP_LIST.fieldday_id":fieldday_id}
                fcurs = self.dbinterface.getdoc(datequery_obj, projection_obj)
                closed_list.append(fcurs[0]["CALENDARMAP_LIST"][0]["date"])
            # next remove entry from calendar map_list
            # ref http://stackoverflow.com/questions/6928354/mongodb-remove-subdocument-from-document
            # db.PHMSA.update({"FIELD_ID":1},{$pull:{CALENDARMAP_LIST:{"fieldday_id":2}}})
            operator = "$pull"
            for fieldday_id in delta_list:
                self.dbinterface.updatedoc(query_obj, operator,
                    {"CALENDARMAP_LIST":{"fieldday_id":fieldday_id}})
            # next decrement all the fieldday_id fields after the entry above
            # was removed so that fieldday_id's are still contiguous
            field_curs = self.dbinterface.getdoc(query_obj, {'_id':0})
            if field_curs.count() > 1:
                # pymongo cursor doc at
                # http://api.mongodb.org/python/current/api/pymongo/cursor.html
                raise SchedulerConfigurationError("fielddbinterface:adjust_config: Query returns more than one document for field_id %d" % (field_id,))
            else:
                totalfielddays = field_curs[0]['TFD']
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
            operator_obj = {'CLOSED_LIST':closed_list}
            self.dbinterface.updatedoc(query_obj, operator, operator_obj,
                upsert_flag=True)
        elif action_type == 'change':
            operator = "$set"
            for delta_dict in delta_list:
                fieldday_id = delta_dict['fieldday_id']
                start_time = delta_dict['starttime']
                end_time = delta_dict['endtime']
                query_obj = {"FIELD_ID":field_id, "CALENDARMAP_LIST.fieldday_id":fieldday_id}
                operator_obj = {"CALENDARMAP_LIST.$.start_time":start_time,
                    "CALENDARMAP_LIST.$.end_time":end_time}
                self.dbinterface.updatedoc(query_obj, operator, operator_obj)
