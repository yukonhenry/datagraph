''' Copyright YukonTR 2013 '''

from schedule_util import getConnectedDivisionGroup
from itertools import groupby
from operator import itemgetter

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
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            # embed div_id value in each dictionary
            flatdiv_list = [{'ROUND_ID':y['ROUND_ID'], 'GAME_TEAM':y['GAME_TEAM'], 'DIV_ID':x['div_id']} for x in connecteddiv_match_list for y in x['match_list']]
            print flatdiv_list
#            flatdiv_list = [y.update({'div_id':x['div_id']}) for x in connecteddiv_match_list] for y in x['match_list']]
            #grouped_list = groupby(connecteddiv_match_list,key=itemgetter('ROUND_ID'))
