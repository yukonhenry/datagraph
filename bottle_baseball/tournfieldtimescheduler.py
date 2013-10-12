''' Copyright YukonTR 2013 '''

from schedule_util import getConnectedDivisionGroup
from itertools import groupby
from operator import itemgetter
from schedule_util import roundrobin
import logging

class TournamentFieldTimeScheduler:
    def __init__(self, dbinterface, field_tuple, divinfo, dindexerGet):
        self.dbinterface = dbinterface
        self.fieldinfo_list = field_tuple.dict_list
        self.findexerGet = field_tuple.indexerGet
        self.connected_div_components = getConnectedDivisionGroup(self.fieldinfo_list)
        self.divinfo_list = divinfo
        self.dindexerGet = dindexerGet

    def generateSchedule(self, totalmatch_list):
        tmindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.dbinterface.dropGameDocuments()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            print 'connectedmatch', connecteddiv_match_list
            # flatten out the list embed div_id value in each dictionary
            # also flatten out 'GAME_TEAM' list generate by the match generator
            flatmatch_list = [{'ROUND_ID':z['ROUND_ID'], 'HOME':p['HOME'], 'AWAY':p['AWAY'], 'DIV_ID':x['div_id']} for x in connecteddiv_match_list for y in x['match_list'] for z in y for p in z['GAME_TEAM']]
            print 'flat', flatmatch_list
            # sort the list according to round_id (needed for groupby below), and then by div_id
            sorted_flatmatch_list = sorted(flatmatch_list, key=itemgetter('ROUND_ID', 'DIV_ID'))
            print 'sort', sorted_flatmatch_list
            # group list by round_id; dict value of 'match_list' key is a nested array,
            # with each inner list corresponding to a specific division
            # the nested list will be passed to the roundrobin multiplexer
            #for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID')):
            #   for key1, items1 in groupby(items, key=itemgetter('DIV_ID')):
            #      for j in items1:
            #         print key, key1, j
            grouped_match_list = [{'round_id':rkey, 'match_list':[[{'home':x['HOME'], 'away':x['AWAY'], 'div_id':dkey} for x in ditems] for dkey, ditems in groupby(ritems, key=itemgetter('DIV_ID'))]} for rkey, ritems in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            #grouped_match_list = [{'round_id':key,'match_list':[[{'HOME':y['HOME'], 'AWAY':y['AWAY'], 'DIV_ID':x['DIV_ID']} for y in x['GAME_TEAM']] for x in items]} for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            logging.debug("tournftscheduler:gensched:groupedlist=%s", grouped_match_list)
            print 'group', grouped_match_list
            for round_games in  grouped_match_list:
                round_id = round_games['round_id']
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    print round_id, rrgame

