#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface
import simplejson as json
from collections import namedtuple
import logging
IDPROPERTY = "TOURNDIV_ID"
gameday_id_CONST = 'GAMEDAY_ID'
start_time_CONST = 'START_TIME'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')
_List_Status_Mode = namedtuple('_List_Status_Mode',
    'list config_status oddnum_mode')

''' class to convert process new tournament schedule.  All namespace conversion between
js object keys and db document keys happen here '''
class TournDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name):
        BaseDBInterface.__init__(self, mongoClient, userid_name, newcol_name,
            DB_Col_Type.TournRR, IDPROPERTY)

    def writeDB(self, divinfo_str, config_status):
        divinfo_list = json.loads(divinfo_str)
        # convert keys to uppercase
        document_list = [{k.upper():v for k,v in x.items()} for x in divinfo_list]
        set_obj = {'CONFIG_STATUS':config_status}
        self.dbinterface.updateInfoDocument(document_list, set_obj, IDPROPERTY)

    def updateDB(self, update_data_str):
        # right now this update operation is hardcoded to update divfield_list
        update_data_list = json.loads(update_data_str)
        for update_obj in update_data_list:
            query_obj = {IDPROPERTY:update_obj['tourndiv_id']}
            # field collection name is an item assocated with divfield list -
            # provides reference col name if dereference field_id is required
            operator_obj = {"DIVFIELD_LIST":update_obj['divfield_list'],
                "FIELDCOL_NAME":update_obj['fieldcol_name']}
            self.dbinterface.updatedoc(query_obj, "$set", operator_obj)

    def readDB(self):
        listresult_tuple = self.dbinterface.getInfoDocument(IDPROPERTY)
        divlist = listresult_tuple.list
        for div in divlist:
            del div['SCHED_TYPE']
            del div['USER_ID']
        result = listresult_tuple.result
        config_status = result['CONFIG_STATUS']
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)

    # read from DB, and convert fieldnames to lower case, but don't convert lists
    # back to string representation
    def readDBraw(self):
        liststatus_tuple = self.dbinterface.getInfoDocument(IDPROPERTY)
        divlist = liststatus_tuple.list
        result = liststatus_tuple.result
        config_status = result['CONFIG_STATUS']
        divinfo_list = [{k.lower():v for k,v in x.items()} for x in divlist]
        return _List_Status(divinfo_list, config_status)
