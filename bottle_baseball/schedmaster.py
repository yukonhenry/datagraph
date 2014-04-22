''' Copyright YukonTR 2014 '''
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from scheddbinterface import SchedDBInterface
from matchgenerator import MatchGenerator
from fieldtimescheduler import FieldTimeScheduleGenerator
from collections import namedtuple
import logging
from sched_exceptions import CodeLogicError
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

# main class for launching schedule generator
# Handling round-robin season-long schedules.  May extend to handle other schedule
# generators.
class SchedMaster:
    def __init__(self, mongoClient, db_type, divcol_name, fieldcol_name, schedcol_name):
        # db_type is for the divinfo schedule attached to the fielddb spec
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
            divinfo_tuple = _List_Indexer(self.divinfo_list,
                self.divinfo_indexerGet)
        else:
            divinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schemaster:init: div config not complete=%s" % (divcol_name,))
        # get field information
        fdbInterface = FieldDBInterface(mongoClient, fieldcol_name)
        fdbtuple = fdbInterface.readDBraw();
        if fdbtuple.config_status == 1:
            self.fieldinfo_list = fdbtuple.list
            self.fieldinfo_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(self.fieldinfo_list)).get(x)
            fieldinfo_tuple = _List_Indexer(self.fieldinfo_list,
                self.fieldinfo_indexerGet)
        else:
            fieldinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schemaster:init: field config not complete=%s" % (fieldcol_name,))
        # create list of div_ids that do not have a 'fields' key
        divreqfields_list = [x['div_id'] for x in self.divinfo_list if 'fields' not in x]
        # if there are div_id's with no 'fields' key, create it
        if divreqfields_list:
            self.divfield_correlate(self.fieldinfo_list, dbInterface, divreqfields_list)
        self.sdbInterface = SchedDBInterface(mongoClient, schedcol_name)
        # save schedule generation parameters in db
        self.sdbInterface.setschedule_param(db_type, divcol_name, fieldcol_name)
        self.fieldtimeScheduleGenerator = FieldTimeScheduleGenerator(
            dbinterface=self.sdbInterface,
            divinfo_tuple=divinfo_tuple, fieldinfo_tuple=fieldinfo_tuple)
        self.schedcol_name = schedcol_name

    def generate(self):
        totalmatch_list = []
        for divinfo in self.divinfo_list:
            totalteams = divinfo['totalteams']
            # possibly rename below to 'totalrounddays' as totalgamedays may not
            # match up to number of physical days
            totalgamedays = divinfo['totalgamedays']
            match = MatchGenerator(totalteams, totalgamedays)
            match_list = match.generateMatchList()
            args_obj = {'div_id':divinfo['div_id'], 'match_list':match_list,
                'numgames_list':match.numgames_list,
                'roundgameslots_num':match.gameslotsperday}
            totalmatch_list.append(args_obj)
        totalmatch_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        totalmatch_tuple = _List_Indexer(totalmatch_list, totalmatch_indexerGet)
        status = self.fieldtimeScheduleGenerator.generateSchedule(totalmatch_tuple)
        return 1 if status else 0


    '''function to add fields key to divinfo_list. Supersedes global function (unnamed) in leaguedivprep'''
    def divfield_correlate(self, fieldinfo_list, dbInterface, div_list):
        for fieldinfo in fieldinfo_list:
            field_id = fieldinfo['field_id']
            for div_id in fieldinfo['primaryuse_list']:
                if div_id in div_list:
                    index = self.divinfo_indexerGet(div_id)
                    if index is not None:
                        divinfo = self.divinfo_list[index]
                        # check existence of key 'fields' - if it exists, append to list of fields, if not create
                        if 'fields' in divinfo:
                            divinfo['fields'].append(field_id)
                        else:
                            divinfo['fields'] = [field_id]
                        dbInterface.updateDBDivFields(divinfo)

    def get_schedule(self, idproperty, propid, div_age="", div_gen=""):
        if idproperty == 'div_id':
            divinfo = self.divinfo_list[self.divinfo_indexerGet(propid)]
            game_list = self.sdbInterface.get_schedule(idproperty,
                div_age=divinfo['div_age'], div_gen=divinfo['div_gen'])
            # also get fields info tied to div
            fieldname_dict= {x:self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['field_name'] for x in divinfo['fields']}
            return {'game_list':game_list, 'fieldname_dict':fieldname_dict}
        elif idproperty == 'field_id':
            fieldinfo = self.fieldinfo_list[self.fieldinfo_indexerGet(propid)]
            game_list = self.sdbInterface.get_schedule(idproperty,
                field_id=fieldinfo['field_id'])
            return {'game_list':game_list}
        elif idproperty == 'team_id':
            game_list = self.sdbInterface.get_schedule(idproperty, team_id=propid,
                div_age=div_age, div_gen=div_gen)
            return {'game_list':game_list}
'''
    def getsched_status(self):
        return self.sdbInterface.getsched_status()
'''
