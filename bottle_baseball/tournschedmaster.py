''' Copyright YukonTR 2014 '''
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from scheddbinterface import SchedDBInterface
from matchgenerator import MatchGenerator
from tournfieldtimescheduler import TournamentFieldTimeScheduleGenerator
from collections import namedtuple
from dateutil import parser
import logging
from sched_exceptions import CodeLogicError
from html import HTML
from random import shuffle, seed
from pprint import pprint

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_List_IndexerGM = namedtuple('List_Indexer', 'dict_list indexerGet indexerMatch')
_List_IndexerM = namedtuple('List_Indexer', 'dict_list indexerMatch')

DIVCONFIG_INCOMPLETE_MASK = 0x1
FIELDCONFIG_INCOMPLETE_MASK = 0x2
PREFINFODATE_ERROR_MASK = 0x4

DB_TYPE = "tourndb"
IDPROPERTY_str = 'tourndiv_id'
# main class for launching schedule generator
# Handling round-robin season-long schedules.  May extend to handle other schedule
# generators.
class TournSchedMaster(object):
    def __init__(self, mongoClient, userid_name, divcol_name, fieldcol_name, schedcol_name):
        self._error_code = 0x0
        self.userid_name = userid_name
        self.sdbInterface = SchedDBInterface(mongoClient, userid_name,
            schedcol_name)
        # db_type is for the divinfo schedule attached to the fielddb spec
        dbInterface = TournDBInterface(mongoClient, userid_name, divcol_name)
        dbtuple = dbInterface.readDBraw()
        if dbtuple.config_status == 1:
            self.divinfo_list = dbtuple.list
            self.divinfo_indexerGet = lambda x: dict((p['tourndiv_id'],i) for i,p in enumerate(self.divinfo_list)).get(x)
            self.divinfo_tuple = _List_Indexer(self.divinfo_list,
                self.divinfo_indexerGet)
        else:
            self.divinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schemaster:init: div config not complete=%s" % (divcol_name,))
            self._error_code |= DIVCONFIG_INCOMPLETE_MASK
        # get field information
        fdbInterface = FieldDBInterface(mongoClient, userid_name, fieldcol_name)
        fdbtuple = fdbInterface.readDBraw();
        if fdbtuple.config_status == 1:
            self.fieldinfo_list = fdbtuple.list
            self.fieldinfo_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(self.fieldinfo_list)).get(x)
            self.fieldinfo_tuple = _List_Indexer(self.fieldinfo_list,
                self.fieldinfo_indexerGet)
        else:
            self.fieldinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schedmaster:init: field config not complete=%s" % (fieldcol_name,))
            self._error_code |= FIELDCONFIG_INCOMPLETE_MASK

        # create list of div_ids that do not have a 'divfield_list' key
        divreqfields_list = [x['div_id'] for x in self.divinfo_list if 'divfield_list' not in x]
        # if there are div_id's with no 'divfield_list' key, create it
        if divreqfields_list:
            self.divfield_correlate(self.fieldinfo_list, dbInterface, divreqfields_list)
        else:
            self.simplifydivfield_list()

        if not self._error_code:
            self.sdbInterface.setschedule_param(DB_TYPE, divcol_name, fieldcol_name)
            self.fieldtimeScheduleGenerator = TournamentFieldTimeScheduleGenerator(
                dbinterface=self.sdbInterface, divinfo_tuple=self.divinfo_tuple,
                fieldinfo_tuple=self.fieldinfo_tuple)
            self.schedcol_name = schedcol_name
            self._xls_exporter = None

    @property
    def xls_exporter(self):
        return self._xls_exporter

    @xls_exporter.setter
    def xls_exporter(self, value):
        self._xls_exporter = value

    @property
    def error_code(self):
        return self._error_code


    def prepGenerate(self):
        totalmatch_list = list()
        for divinfo in self.divinfo_list:
            tourndiv_id = divinfo[IDPROPERTY_str]
            print tourndiv_id
            totalteams = divinfo['totalteams']
            team_list = self.getTeamID_list(totalteams)
            totalgamedays = divinfo['totalgamedays']
            minbracket_size = totalgamedays+1
            brackets_num = totalteams / minbracket_size
            running_index = 0
            bracket_team_list = list()
            index = 0
            match_list = list()
            for bracket_id in range(1, brackets_num+1):
                if totalteams - (index+minbracket_size) >= minbracket_size:
                    bracket_size = minbracket_size
                else:
                    bracket_size = totalteams - index
                running_index += bracket_size
                team_id_list = team_list[index:running_index]
                bracket_dict = {'bracket_id':bracket_id,
                    'team_id_list':team_id_list}
                # calculate virtual number of game days required as parameter for
                # MatchGenerator object.  Value is equal to #games if #teams is even,
                # if odd, add one to #games.
                vgames_num = totalgamedays if bracket_size%2==0 else totalgamedays+1
                match = MatchGenerator(bracket_size, vgames_num,
                    maxGamesPerTeam=totalgamedays)
                bracket_match_list = match.generateMatchList(
                    teamid_map=team_id_list)
                match_list.append(bracket_match_list)
                bracket_team_list.append(bracket_dict)
                index = running_index
            totalmatch_list.append({IDPROPERTY_str: divinfo[IDPROPERTY_str],
                'match_list':match_list, 'max_round':vgames_num})
        self.fieldtimeScheduleGenerator.generateSchedule(totalmatch_list)
        status = True
        return 1 if status else 0
    def generate(self):
        totalmatch_list = []
        totalbyeteam_list = list()
        for divinfo in self.divinfo_list:
            totalteams = divinfo['totalteams']
            # possibly rename below to 'totalrounddays' as totalgamedays may not
            # match up to number of physical days
            totalgamedays = divinfo['totalgamedays']
            div_id = divinfo['div_id']
            match = MatchGenerator(totalteams, totalgamedays,
                oddnumplay_mode=self.oddnumplay_mode)
            match_list = match.generateMatchList()
            args_obj = {'div_id':div_id, 'match_list':match_list,
                'numgames_perteam_list':match.numgames_perteam_list,
                'gameslots_perrnd_perdiv':match.gameslotsperday}
            totalmatch_list.append(args_obj)
            if self.oddnumplay_mode and match.byeteam_list:
                totalbyeteam_list.append({'div_id':div_id, 'byeteam_list':match.byeteam_list})
        totalmatch_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        totalmatch_tuple = _List_Indexer(totalmatch_list, totalmatch_indexerGet)
        status = self.fieldtimeScheduleGenerator.generateSchedule(
            totalmatch_tuple, self.oddnumplay_mode, totalbyeteam_list)
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

    def simplifydivfield_list(self):
        ''' create a simplified version of the divfield_list which only
        includes the field_id's - the only value necessary for schedule
        creation; ignore other items such as field name '''
        for divinfo in self.divinfo_list:
            if 'divfield_list' in divinfo:
                new_list = [x['field_id'] for x in divinfo['divfield_list']]
                divinfo['divfield_list'] = new_list

    def get_schedule(self, idproperty, propid, div_age="", div_gen=""):
        if idproperty == 'tourndiv_id':
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

    def getHTMLTeamTable(self, div_age, div_gen, team_id):
        # https://pypi.python.org/pypi/html/
        return_dict = self.get_schedule('team_id', team_id,
            div_age=div_age, div_gen=div_gen)
        game_list = return_dict['game_list']
        html = HTML()
        table = html.table(width='100%', border='1px solid black')
        table.caption(self.userid_name+" "+self.schedcol_name+" "+div_age+div_gen+str(team_id))
        header_row = table.tr
        header_row.th('Game Date', padding='5px')
        header_row.th('Start Time', padding='5px')
        header_row.th('Field', padding='5px')
        header_row.th('Home', padding='5px')
        header_row.th('Away', padding='5px')
        for game in game_list:
            game_row = table.tr
            game_row.td(game['game_date'])
            game_row.td(game['start_time'])
            findex = self.fieldinfo_indexerGet(game['venue'])
            if findex is not None:
                field_name = self.fieldinfo_list[findex]['field_name']
                game_row.td(field_name)
            game_row.td(str(game['home']))
            game_row.td(str(game['away']))
        return str(html)

    def getTeamID_list(self, numteams):
        team_id_list = range(1,numteams+1)
        # ref http://docs.python.org/2/library/random.html#random.shuffle
        # doc above for random shuffle (e.g. for an)
        # start the seed with same number so random functions generates
        # same resuts from run to run/
        seed(0)
        shuffle(team_id_list)
        return team_id_list
