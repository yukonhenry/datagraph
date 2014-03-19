''' Copyright YukonTR 2014 '''
from tourndbinterface import TournDBInterface
from fielddbinterface import FieldDBInterface
from rrdbinterface import RRDBInterface
from matchgenerator import MatchGenerator
import logging
from sched_exceptions import CodeLogicError
class SchedMaster:
    def __init__(self, mongoClient, db_type, divcol_name, field_colname):
        if db_type == 'rrdb':
            dbInterface = RRDBInterface(mongoClient, divcol_name)
        elif db_type == 'tourndb':
            dbInterface = TournDBInterface(mongoClient, divcol_name)
        else:
            raise CodeLogicError("schemaster:init: db_type not recognized db_type=%s" % (db_type,))
        dbtuple = dbInterface.readDB();
        if dbtuple.config_status == 1:
            self.divinfo_list = dbtuple.list
        else:
            self.divinfo_list = None
            raise CodeLogicError("schemaster:init: div config not complete=%s" % (divcol_name,))
        # get field information
        fdbInterface = FieldDBInterface(mongoClient, field_colname)
        fdbtuple = fdbInterface.readDB();
        if fdbtuple.config_status == 1:
            self.fieldinfo_list = fdbtuple.list
        else:
            self.fieldinfo_list = None
            raise CodeLogicError("schemaster:init: field config not complete=%s" % (field_colname,))

    def generate(self):
        total_match_list = []
        for divinfo in self.divinfo_list:
            totalteams = divinfo['totalteams']
            totalgamedays = divinfo['totalgamedays']
            match = MatchGenerator(totalteams, totalgamedays)
            match_list = match.generateMatchList()
            args_obj = {'div_id':divinfo['div_id'], 'match_list':match_list,
                'numgames_list':match.numGames_list,
                'gameslotsperday':match.gameslotsperday}
            total_match_list.append(args_obj)
        print 'totalmatch', total_match_list

