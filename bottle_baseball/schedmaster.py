''' Copyright YukonTR 2014 '''
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from matchgenerator import MatchGenerator
from fieldtimescheduler import FieldTimeScheduleGenerator
from collections import namedtuple
import logging
from sched_exceptions import CodeLogicError
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class SchedMaster:
    def __init__(self, mongoClient, db_type, divcol_name, field_colname):
        if db_type == 'rrdb':
            dbInterface = RRDBInterface(mongoClient, divcol_name)
        elif db_type == 'tourndb':
            dbInterface = TournDBInterface(mongoClient, divcol_name)
        else:
            raise CodeLogicError("schemaster:init: db_type not recognized db_type=%s" % (db_type,))
        dbtuple = dbInterface.readDBraw();
        if dbtuple.config_status == 1:
            self.divinfo_list = dbtuple.list
            self.divinfo_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.divinfo_list)).get(x)
        else:
            self.divinfo_list = None
            raise CodeLogicError("schemaster:init: div config not complete=%s" % (divcol_name,))
        # get field information
        fdbInterface = FieldDBInterface(mongoClient, field_colname)
        fdbtuple = fdbInterface.readDBraw();
        if fdbtuple.config_status == 1:
            fieldinfo_list = fdbtuple.list
            self.divfield_correlate(fieldinfo_list)
        else:
            fieldinfo_list = None
            raise CodeLogicError("schemaster:init: field config not complete=%s" % (field_colname,))
        self.fieldtimeScheduleGenerator = FieldTimeScheduleGenerator(dbinterface=dbInterface, fdbinterface=fdbInterface,
            divinfo_list=self.divinfo_list,
            divinfo_indexerGet=self.divinfo_indexerGet,
            fieldinfo_list=fieldinfo_list)

    def generate(self):
        totalmatch_list = []
        for divinfo in self.divinfo_list:
            totalteams = divinfo['totalteams']
            totalgamedays = divinfo['totalgamedays']
            match = MatchGenerator(totalteams, totalgamedays)
            match_list = match.generateMatchList()
            args_obj = {'div_id':divinfo['div_id'], 'match_list':match_list,
                'numgames_list':match.numGames_list,
                'gameslotsperday':match.gameslotsperday}
            totalmatch_list.append(args_obj)
        totalmatch_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.fieldtimeScheduleGenerator.generateSchedule(totalmatch_list,
            totalmatch_indexerGet)


    '''function to add fields key to divinfo_list. Supersedes global function (unnamed) in leaguedivprep'''
    def divfield_correlate(self, fieldinfo_list):
        for fieldinfo in fieldinfo_list:
            field_id = fieldinfo['field_id']
            for div_id in fieldinfo['primaryuse_list']:
                index = self.divinfo_indexerGet(div_id)
                if index is not None:
                    divinfo = self.divinfo_list[index]
                    # check existence of key 'fields' - if it exists, append to list of fields, if not create
                    if 'fields' in divinfo:
                        divinfo['fields'].append(field_id)
                    else:
                        divinfo['fields'] = [field_id]


