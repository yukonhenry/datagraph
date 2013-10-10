''' Copyright YukonTR 2013 '''

from leaguedivprep import getConnectedDivisions
class TournamentFieldTimeScheduler:
    def __init__(self, dbinterface, field_tuple):
        self.dbinterface = dbinterface
        self.fieldinfo_list = field_tuple.dict_list
        self.findexerGet = field_tuple.indexerGet

    def generateSchedule(self, totalmatch_list):
    	print totalmatch_list

