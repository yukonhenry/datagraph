from dbinterface import MongoDBInterface
from random import shuffle, seed
import logging
from sched_exceptions import CodeLogicError
from matchgenerator import MatchGenerator
from tournfieldtimescheduler import TournamentFieldTimeScheduler
from tourndbinterface import TournDBInterface
from schedule_util import any_ismore, any_isless
from sched_exporter import ScheduleExporter

class TournamentScheduler:
    def __init__(self, mongoClient, divinfo_col, tfield_tuple):
        #self.dbInterface = MongoDBInterface(mongoClient, divinfo_col, rr_type_flag=False)
        self.tdbInterface = TournDBInterface(mongoClient, divinfo_col)
        divinfo_tuple = self.tdbInterface.readDB()
        self.tourn_divinfo = divinfo_tuple.dict_list
        self.tindexerGet = divinfo_tuple.indexerGet
        self.tfield_tuple = tfield_tuple

    def prepGenerate(self):
        totalmatch_list = []
        for division in self.tourn_divinfo:
            nt = int(division['totalteams'])
            team_id_list = self.getTeamID_list(nt)
            nb = int(division['totalbrackets'])
            ne = int(division['elimination_num'])
            div_id = int(division['div_id'])
            bracket_list = self.createRRBrackets(nt, team_id_list, nb)
            logging.debug("tournsched:createRRbrack: div_id= %d bracket_list=%s",
                          div_id, bracket_list)
            print 'div_id bracketlist', div_id, bracket_list
            # number games per team in bracket is the minimum bracket size minus 1
            # all brackets in the division has the same number of games, e.g.
            # if one bracket has three teams and another has four, each team plays
            # 2 games
            ng = nt/nb - 1
            # calculate virtual number of game days required as parameter for
            # MatchGenerator object.  Value is equal to #games if #teams is even,
            # if odd, add one to #games.
            virtualgamedays = ng if nt%2==0 else ng+1
            logging.info("tournscheduler:prepGenerate: virtualgamedays=%d",
                         virtualgamedays)
            match_list = []
            partialgame_list = []
            for bracket in bracket_list:
                match = MatchGenerator(len(bracket['team_id_list']), virtualgamedays, maxGamesPerTeam=ng)
                bracket_match_list = match.generateMatchList(teamid_map=bracket['team_id_list'])
                logging.info("tournscheduler:prepGenerate:div=%d bracket=%s bracketmatch_list=%s",
                             div_id, bracket, bracket_match_list)
                print 'div bracket numgames', div_id, bracket, match.numGames_list
                if any_isless(match.numGames_list, ng):
                    index_list = [i for i,j in enumerate(match.numGames_list) if j < ng]
                    partialgame_list.append([bracket['team_id_list'][x] for x in index_list])
                match_list.append(bracket_match_list)
            if partialgame_list:
                # create cross-bracket matches if necessary
                if len(partialgame_list) != 2:
                    raise CodeLogicError("TournScheduler:PrepGenerate: need to add handling for partial game list that has other than 2 sets")
                else:
                    game_team_list = [{'HOME':i,'AWAY':j} for i,j in zip(partialgame_list[0], partialgame_list[1])]
                    print 'PARTIAL GAMETEAMLIST', game_team_list
                    match_list.append([{'ROUND_ID':virtualgamedays,
                                      'GAME_TEAM':game_team_list}])

            totalmatch_list.append({'div_id': division['div_id'],
                                    'match_list':match_list})
        tourn_ftscheduler = TournamentFieldTimeScheduler(self.tdbInterface, self.tfield_tuple,
                                                         self.tourn_divinfo,
                                                         self.tindexerGet)
        tourn_ftscheduler.generateSchedule(totalmatch_list)
        tschedExporter = ScheduleExporter(self.tdbInterface.dbInterface)
        for division in self.tourn_divinfo:
            tschedExporter.exportDivTeamSchedules(div_id=int(division['div_id']), age=division['div_age'], gen=division['div_gen'],
                                                  numteams=int(division['totalteams']),
                                                  prefix='PHMSACup2013')
        tschedExporter.exportTeamSchedules(div_id=int(division['div_id']), age=division['div_age'], gen=division['div_gen'],
                                             numteams=int(division['totalteams']), prefix='PHMSACup2013')
        tschedExporter.exportDivSchedules(division['div_id'])
        #tschedExporter.exportDivSchedulesRefFormat(prefix='PHMSACup2013')

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

        return bracket_list
