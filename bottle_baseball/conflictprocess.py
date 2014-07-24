''' Copyright YukonTR 2014 '''
import logging
from operator import itemgetter

class ConflictProcess(object):
    def __init__(self, conflictinfo_list, prefinfo_list):
        for x in conflictinfo_list:
            # add key value to dict elements - list comprehension does
            # note work as x.update works in-memory and returns None
            x.update({'schedflag':False})
        self.conflictinfo_list = conflictinfo_list
        self.prefinfo_list = prefinfo_list
        self.cindexerMatch = lambda x: [i for i,p in
            enumerate(self.conflictinfo_list) if p['div_1_id']==x or
            p['div_2_id']==x]
        self.normconflict_list = self.normalize(conflictinfo_list)
        self.nindexerMatch = lambda x: [i for i,p in
            enumerate(self.normconflict_list) if p['div_id']==x]

    def process(self, cdiv_list):
        for div_id in cdiv_list:
            # get all indices corresponding to current div_id
            index_list = self.cindexerMatch(div_id)
            # get list of conflicts that involve reference div
            conflict_list = [self.conflictinfo_list[index]
                for index in index_list]
            for conflict in conflict_list:
                if not conflict['schedflag']:
                    # get reference team_id and conflict div and team_id's
                    # given reference div_id
                    if conflict['div_1_id'] == div_id:
                        team_id = confict['team_1_id']
                        conflictdiv_id = conflict['div_2_id']
                        conflictteam_id = conflict['team_2_id']
                    else:
                        team_id = confict['team_2_id']
                        conflictdiv_id = conflict['div_1_id']
                        conflictteam_id = conflict['team_1_id']
                    conflict['schedflag'] = True

    def normalize(self, cinfo_list):
        # flatten conflict_list - create two entries for each conflict pair
        # eacy keyed off of div_id, team_id pair
        # Map (div_1_id, team_1_id, div_2_id, team_2_id) to 2 entries of
        # (div_id, team_id, conflict_div_id, conflict_team_id)
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

    '''
    @property
    def tminfo_list(self):
        return self._tminfo_list

    @tminfo_list.setter
    def tminfo_list(self, value):
        self._tminfo_list = value

    @property
    def tminfo_indexerGet(self):
        return self._tminfo_indexerGet

    @tminfo_indexerGet.setter
    def tminfo_indexerGet(self, value):
        self._tminfo_indexerGet = value

    @property
    def tminfo_indexerMatch(self):
        return self._tminfo_indexerMatch

    @tminfo_indexerMatch.setter
    def tminfo_indexerMatch(self, value):
        self._tminfo_indexerMatch = value
    '''

