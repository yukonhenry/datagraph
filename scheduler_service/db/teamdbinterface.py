#!/usr/bin/python
''' Copyright YukonTR 2014 '''
import simplejson as json
from util.schedule_util import convertJStoPY_daylist, convertPYtoJS_daylist
from dbinterface import DB_Col_Type
from basedbinterface import BaseDBInterface
from collections import namedtuple

_PlusList_Status = namedtuple('_PlusList_Status', 'list config_status divstr_colname divstr_db_type')
class TeamDBInterface(BaseDBInterface):
    def __init__(self, mongoClient, userid_name, newcol_name, sched_cat):
        BaseDBInterface.__init__(self, mongoClient, userid_name,
            newcol_name, sched_cat,
            DB_Col_Type.TeamInfo, 'DT_ID')

    def check_docexists(self):
        # use DT_ID key to see if any teaminfo doc exists
        return self.dbinterface.check_docexists("DT_ID")

    def writeDB(self, info_str, config_status, divstr_colname, divstr_db_type):
        info_list = json.loads(info_str)
        for info in  info_list:
            info['dt_id'] = "dv"+str(info['div_id'])+"tm"+str(info['tm_id'])
            if info['prefdays']:
                temp_list = [int(x) for x in info['prefdays'].split(',')]
                info['prefdays'] = convertJStoPY_daylist(temp_list)
            else:
                info['prefdays'] = []
        document_list = [{k.upper():v for k,v in x.items()} for x in info_list]
        self.dbinterface.updateInfoPlusDocument(document_list, config_status,
            divstr_colname=divstr_colname, divstr_db_type=divstr_db_type,
            id_str=self.capid_str)

    def readDB(self):
        # readDB is for returning to client UI
        liststatus_qtuple = self.dbinterface.getInfoPlusDocument(self.capid_str)
        rawlist = liststatus_qtuple.list
        config_status = liststatus_qtuple.config_status
        divstr_colname = liststatus_qtuple.divstr_colname
        divstr_db_type = liststatus_qtuple.divstr_db_type
        for raw in rawlist:
            del raw['SCHED_TYPE']
            del raw['USER_ID']
            del raw['SCHED_CAT']
            temp_list = convertPYtoJS_daylist(raw['PREFDAYS'])
            del raw['PREFDAYS']
            raw['prefdays'] = ','.join(str(f) for f in temp_list)
        # ref http://stackoverflow.com/questions/17933168/replace-dictionary-keys-strings-in-python
        # switch key to lower case for transfer to client
        info_list = [{k.lower():v for k,v in x.items()} for x in rawlist]
        return _PlusList_Status(info_list, config_status, divstr_colname,
            divstr_db_type)
