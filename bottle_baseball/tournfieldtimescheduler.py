''' Copyright YukonTR 2013 '''

from leaguedivprep import getConnectedDivisions

class TournamentFieldTimeScheduler:
    def __init__(self, dbinterface, field_tuple, divinfo, dindexerGet):
        self.dbinterface = dbinterface
        self.fieldinfo_list = field_tuple.dict_list
        self.findexerGet = field_tuple.indexerGet
        self.connected_div_components = getConnectedDivisions()
        self.divinfo_list = divinfo
        self.dindexerGet = dindexerGet

    def generateSchedule(self, totalmatch_list):
	    self.dbinterface.dropGameDocuments()  # reset game schedule collection
	    for connected_div_list in self.connected_div_components:
	    	for div_id in connected_div_list:
	    		print 'divid indexerget', div_id, self.dindexerGet(div_id)
	    		divinfo = self.divinfo_list[self.dindexerGet(div_id)]
	    		print 'divid divinfo', div_id, divinfo

