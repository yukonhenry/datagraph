''' Copyright YukonTR 2014 '''
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from scheddbinterface import SchedDBInterface
from prefdbinterface import PrefDBInterface
from teamdbinterface import TeamDBInterface
from conflictdbinterface import ConflictDBInterface
from matchgenerator import MatchGenerator
from fieldtimescheduler import FieldTimeScheduleGenerator
from collections import namedtuple
import logging
from sched_exceptions import CodeLogicError
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_List_IndexerGM = namedtuple('List_Indexer', 'dict_list indexerGet indexerMatch')
_List_IndexerM = namedtuple('List_Indexer', 'dict_list indexerMatch')


# main class for launching schedule generator
# Handling round-robin season-long schedules.  May extend to handle other schedule
# generators.
class SchedMaster:
    def __init__(self, mongoClient, db_type, divcol_name, fieldcol_name, schedcol_name, prefcol_name=None, conflictcol_name=None):
        self.sdbInterface = SchedDBInterface(mongoClient, schedcol_name)
        # db_type is for the divinfo schedule attached to the fielddb spec
        if db_type == 'rrdb':
            dbInterface = RRDBInterface(mongoClient, divcol_name)
        elif db_type == 'tourndb':
            dbInterface = TournDBInterface(mongoClient, divcol_name)
        else:
            raise CodeLogicError("schemaster:init: db_type not recognized db_type=%s" % (db_type,))
        dbtuple = dbInterface.readDBraw()
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
            self.fieldinfo_tuple = _List_Indexer(self.fieldinfo_list,
                self.fieldinfo_indexerGet)
        else:
            self.fieldinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schedmaster:init: field config not complete=%s" % (fieldcol_name,))
        # create list of div_ids that do not have a 'divfield_list' key
        divreqfields_list = [x['div_id'] for x in self.divinfo_list if 'divfield_list' not in x]
        # if there are div_id's with no 'divfield_list' key, create it
        if divreqfields_list:
            self.divfield_correlate(self.fieldinfo_list, dbInterface, divreqfields_list)
        else:
            self.simplifydivfield_list()
        # get team-related field affinity information, if any
        # use divcol_name as it shares collection name w divinfo
        tmdbInterface = TeamDBInterface(mongoClient, divcol_name)
        if tmdbInterface.check_docexists():
            tmdbtuple = tmdbInterface.readDBraw()
            # recreate tminfo_list from db read, but leave out fields such as
            # team name which is not needed for schedule generation
            tminfo_list = [{'dt_id':x['dt_id'], 'div_id':x['div_id'],
                'tm_id':x['tm_id'], 'af_list':x['af_list']}
                for x in tmdbtuple.list]
            # indexerGet for specific div_id and team_id match
            tminfo_indexerGet = lambda x: dict((p['dt_id'],i) for i,p in enumerate(tminfo_list)).get("dv"+str(x[0])+"tm"+str(x[1]))
            # indexermatch for list of team matches for specified div_id
            tminfo_indexerMatch = lambda x: [i for i,p in enumerate(tminfo_list) if p['div_id'] == x]
            # _List_IndexerM gets dereferenced using indexerMatch instead of
            # indexerGet
            tminfo_tuple = _List_IndexerGM(tminfo_list, tminfo_indexerGet,
                tminfo_indexerMatch)
        else:
            tminfo_tuple = None
        # get pref list information, if any
        if prefcol_name:
            # preference list use is optional - only process if preference list
            # exists
            pdbInterface = PrefDBInterface(mongoClient, prefcol_name)
            pdbtuple = pdbInterface.readDBraw();
            if pdbtuple.config_status == 1:
                prefinfo_list = pdbtuple.list
                prefinfo_indexerGet = lambda x: dict((p['pref_id'],i) for i,p in enumerate(prefinfo_list)).get(x)
                prefinfo_indexerMatch = lambda x: [i for i,p in
                    enumerate(prefinfo_list) if p['div_id'] == x]
                prefinfo_triple = _List_IndexerGM(prefinfo_list,
                    prefinfo_indexerGet, prefinfo_indexerMatch)
            else:
                prefinfo_triple = None
                # raise error as client should only be displaying in select widget
                # conflict lists that have config status complete
                raise CodeLogicError("schedmaster:init: pref config not complete=%s" % (prefcol_name,))
        else:
            pdbInterface = None
            prefinfo_triple = None

        if conflictcol_name:
            cdbInterface = ConflictDBInterface(mongoClient, conflictcol_name)
            cdbtuple = cdbInterface.readDBraw()
            if cdbtuple.config_status == 1:
                conflictinfo_list = cdbtuple.list
                #cindexerGet = lambda x: dict((p['conflict_id'],i) for i,p in enumerate(conflictinfo_list)).get(x)
                #conflictinfo_tuple = _List_Indexer(conflictinfo_list, cindexerGet)
            else:
                conflictinfo_list = None
                #conflictinfo_tuple = None
                # raise error as client should only be displaying in select widget
                # conflict lists that have config status complete
                raise CodeLogicError("schedmaster:init: conflict config not complete=%s" % (conflictcol_name,))
        else:
            conflictinfo_list = None
            #conflictinfo_tuple = None
        self.sdbInterface.setschedule_param(db_type, divcol_name, fieldcol_name,
            prefcol_name=prefcol_name, conflictcol_name=conflictcol_name)
        self.fieldtimeScheduleGenerator = FieldTimeScheduleGenerator(
            dbinterface=self.sdbInterface, divinfo_tuple=divinfo_tuple,
            fieldinfo_tuple=self.fieldinfo_tuple,
            prefinfo_triple=prefinfo_triple, pdbinterface=pdbInterface,
            tminfo_tuple=tminfo_tuple, conflictinfo_list=conflictinfo_list,
            cdbinterface=cdbInterface)
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
                'numgames_perteam_list':match.numgames_perteam_list,
                'gameslots_perrnd_perdiv':match.gameslotsperday}
            totalmatch_list.append(args_obj)
        totalmatch_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        totalmatch_tuple = _List_Indexer(totalmatch_list, totalmatch_indexerGet)
        status = self.fieldtimeScheduleGenerator.generateSchedule(totalmatch_tuple)
        return 1 if status else 0


    '''function to add fields key to divinfo_list. Supersedes global function (unnamed) in leaguedivprep'''
    def divfield_correlate(self, fieldinfo_list, dbInterface, div_list):
        # use set to keep track of unique div_id's that have fields attached to them
        divset = set()
        for fieldinfo in fieldinfo_list:
            field_id = fieldinfo['field_id']
            for div_id in fieldinfo['primaryuse_list']:
                if div_id in div_list:
                    index = self.divinfo_indexerGet(div_id)
                    if index is not None:
                        divset.update(div_id)
                        divinfo = self.divinfo_list[index]
                        # check existence of key 'divfield_list' - if it exists, append to list of fields, if not create
                        if 'divfield_list' in divinfo:
                            divinfo['divfield_list'].append(field_id)
                        else:
                            divinfo['divfield_list'] = [field_id]
        '''
        # save to db
        for div_id in divset:
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            dbInterface.updateDBDivFields(divinfo)
        '''

    def simplifydivfield_list(self):
        for divinfo in self.divinfo_list:
            if 'divfield_list' in divinfo:
                new_list = [x['field_id'] for x in divinfo['divfield_list']]
                divinfo['divfield_list'] = new_list

    def get_schedule(self, idproperty, propid, div_age="", div_gen=""):
        if idproperty == 'div_id':
            divinfo = self.divinfo_list[self.divinfo_indexerGet(propid)]
            game_list = self.sdbInterface.get_schedule(idproperty,
                div_age=divinfo['div_age'], div_gen=divinfo['div_gen'])
            # also get fields info tied to div
            fieldname_dict= {x:self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['field_name'] for x in divinfo['divfield_list']}
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
        elif idproperty == 'fair_id':
            # get fairness metrics
            # get divinfo as fairness metric calculations require divinfo
            # parameters
            divinfo = self.divinfo_list[self.divinfo_indexerGet(propid)]
            metrics_list = self.sdbInterface.get_schedule(idproperty,
                div_age=div_age, div_gen=div_gen, divinfo=divinfo,
                fieldinfo_tuple=self.fieldinfo_tuple)
            divfield_list = [{'field_id':x,
                'field_name':self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['field_name']}
                for x in divinfo['divfield_list']]
            return {'metrics_list':metrics_list, 'divfield_list':divfield_list}
