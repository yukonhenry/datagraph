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
            grouped_list = groupby(connecteddiv_match_list,key=itemgetter('ROUND_ID'))
