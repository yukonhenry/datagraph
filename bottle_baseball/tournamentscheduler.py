from dbinterface import MongoDBInterface
from random import shuffle, seed
import logging
from sched_exceptions import CodeLogicError
from matchgenerator import MatchGenerator

totalteams_CONST = 'TOTALTEAMS'
totalbrackets_CONST = 'TOTALBRACKETS'
elimination_num_CONST = 'ELIMINATION_NUM'

class TournamentScheduler:
    def __init__(self, mongoClient, divinfo_col):
        self.dbInterface = MongoDBInterface(mongoClient, divinfo_col, rr_type_flag=False)
        divinfo_tuple = self.dbInterface.getTournamentDivInfo()
        self.tourn_divinfo = divinfo_tuple.dict_list
        self.tindexerGet = divinfo_tuple.indexerGet

    def prepGenerate(self):
         for division in self.tourn_divinfo:
             nt = int(division[totalteams_CONST])
             team_id_list = self.getTeamID_list(nt)
             nb = int(division[totalbrackets_CONST])
             ne = int(division[elimination_num_CONST])
             bracket_list = self.createRRBrackets(nt, team_id_list, nb)
             for bracket in bracket_list:
                 match = MatchGenerator(len(bracket['team_id_list']), 3)
                 match_list = match.generateMatchList()
                 logging.info("tournscheduler:prepGenerate:bracket=%s match_list=%s",
                              bracket, match_list)
                 print 'bracket matchlist', bracket, match_list

    def getTeamID_list(self, numteams):
        team_id_list = range(1,numteams+1)
        # ref http://docs.python.org/2/library/random.html#random.shuffle
        # doc above for random shuffle (e.g. for an)
        # start the seed with same number so random functions generates
        # same resuts from run to run/
        seed(0)
        shuffle(team_id_list)
        return team_id_list
        
    def createRRBrackets(self, numteams, team_list, numbrackets):
        if len(team_list) != numteams:
            raise CodeLogicError("tournscheduler:createRRBrackets: team list len error")
        min_per_brack = numteams/numbrackets
        max_per_brack = min_per_brack + 1
        numbracks_max = numteams % numbrackets
        numbracks_min = numbrackets - numbracks_max
        index = 0
        bracket_list = []
        for bracket_id in range(1, numbrackets+1):
            bracketsize = min_per_brack if bracket_id <= numbracks_min else max_per_brack
            lastindex = index + bracketsize
            team_id_list = team_list[index:lastindex]
            bracket_dict = {'bracket_id':bracket_id, 'team_id_list':team_id_list}
            bracket_list.append(bracket_dict)
            index = lastindex
        logging.debug("tournsched:createRRbrack: bracket_list=%s", bracket_list)
        print 'bracketlist', bracket_list
        return bracket_list
        
    def matchGenerate(self, nt, nb, ne):
        self.numTeams = nt
        self.numBrackets = nb