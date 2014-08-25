''' Copyright YukonTR 2014 '''
import logging
from operator import itemgetter
from datetime import timedelta
from collections import namedtuple

_Pref_Fixed_tuple = namedtuple('_Pref_Fixed_tuple', 'pref_list fixteam_list')
class ConflictProcess(object):
    def __init__(self, conflictinfo_list, divinfo_tuple, cdbinterface):
        ''' Perform preprocessing for the conflict specification generated
        from configuration '''
        for x in conflictinfo_list:
            # add key value to dict elements - list comprehension does
            # note work as x.update works in-memory and returns None
            x.update({'schedflag':False})
        self.conflictinfo_list = conflictinfo_list
        self.cindexerMatch = lambda x: [i for i,p in
            enumerate(self.conflictinfo_list) if p['div_1_id']==x or
            p['div_2_id']==x]
        self.normconflict_list = self.normalize(conflictinfo_list)
        self.nindexerMatch = lambda x: [i for i,p in
            enumerate(self.normconflict_list) if p['div_id']==x]
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        self.cdbinterface = cdbinterface

    def process(self, cdiv_list, connected_sched_list, conindexerGet, pref_len):
        ''' process conflict list and for each conflict generate entries into
        preference list.  The current conflict resolution method is based onl
        converting a conflict list into a preference list by assuming one of
        team has a fixed schedule, and based on the assumption, generating a
        preference time list for the other time.  One key here is that th
        schedule for the reference team needs to be fixed and not be manipulated
        during later match swapping for preference satisfaction'''
        pref_id = pref_len + 1 # starting pref id
        pref_list = list()
        fixteam_list = list()
        for div_id in cdiv_list:
            # get all indices corresponding to current div_id
            index_list = self.cindexerMatch(div_id)
            if not index_list:
                continue
            # get list of conflicts that involve reference div
            conflict_list = [self.conflictinfo_list[index]
                for index in index_list]
            for conflict in conflict_list:
                if not conflict['schedflag']:
                    priority = conflict['priority']
                    # get reference team_id and conflict div and team_id's
                    # given reference div_id
                    if conflict['div_1_id'] == div_id:
                        team_id = conflict['team_1_id']
                        conflictdiv_id = conflict['div_2_id']
                        conflictteam_id = conflict['team_2_id']
                    else:
                        team_id = confict['team_2_id']
                        conflictdiv_id = conflict['div_1_id']
                        conflictteam_id = conflict['team_1_id']
                    fixteam_list.append({'div_id':div_id, 'team_id':team_id})
                    divinfo = self.divinfo_list[self.dindexerGet(div_id)]
                    gameinterval = divinfo['gameinterval']
                    gameinterval_td = timedelta(0,0,0,0,gameinterval)
                    # get parameters necessary to retrieve schedule involving
                    # div_id and team_id
                    divsched_list = connected_sched_list[conindexerGet(div_id)]['sched_list']
                    sindexerMatch = lambda x: [i for i,p in
                        enumerate(divsched_list) if p['home_id']==x or
                        p['away_id']==x]
                    index_list = sindexerMatch(team_id)
                    teamsched_list = [divsched_list[index]
                        for index in index_list]
                    conflict_id = conflict['conflict_id']
                    # initialize counter to count how many preference list entries
                    # generated for each conflict
                    genpref_count = 0
                    for teamsched in teamsched_list:
                        # use fieldday and fieldday_id info to get either
                        # standard or custom start and end times. Custom
                        # start/end times will be embedded in the calendarmap_list
                        field_id = teamsched['field_id']
                        fieldday_id = teamsched['fieldday_id']
                        start_time_dt = teamsched['start_time']
                        # we will create the preference for subsequent scheduling
                        # of the conflictdiv and conflictteam to end their game
                        # before the reference team start time and start after
                        # the reference team match ends
                        pref_dict = {'pref_id':pref_id, 'priority':priority,
                            'div_id':conflictdiv_id, 'team_id':conflictteam_id,
                            'game_date':teamsched['game_date'].date(),
                            'end_before_dt':start_time_dt,
                            'start_after_dt':start_time_dt+gameinterval_td,
                            'field_id':teamsched['field_id'],
                            'fieldday_id':teamsched['fieldday_id'],
                            'conflict_id':conflict_id}
                        pref_list.append(pref_dict)
                        genpref_count += 1
                        pref_id += 1
                    conflict['schedflag'] = True
                    self.cdbinterface.addconflict_prefcount(conflict_id,
                        genpref_count)
        return _Pref_Fixed_tuple(pref_list, fixteam_list)

    def normalize(self, cinfo_list):
        # flatten conflict_list - create two entries for each conflict pair
        # eacy keyed off of div_id, team_id pair
        # Map (div_1_id, team_1_id, div_2_id, team_2_id) to 2 entries of
        # (div_id, team_id, conflictdiv_id, conflictteam_id)
        # number of conflict entries will double
        normalized_cinfo_list = [{'nconflict_id':i, 'priority':x['priority'],
            'div_id':x['div_1_id'], 'team_id':x['team_1_id'],
            'condiv_id':x['div_2_id'], 'conteam_id':x['team_2_id']}
            for i,x in enumerate(cinfo_list, start=1)]
        list_len = len(cinfo_list)
        normalized_cinfo_list.extend([{'nconflict_id':i, 'priority':x['priority'],
            'div_id':x['div_2_id'], 'team_id':x['team_2_id'],
            'condiv_id':x['div_1_id'], 'conteam_id':x['team_1_id']}
            for i,x in enumerate(cinfo_list, start=list_len+1)])
        return normalized_cinfo_list
