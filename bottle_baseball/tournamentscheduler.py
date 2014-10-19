from dbinterface import MongoDBInterface
from random import shuffle, seed
import logging
from sched_exceptions import CodeLogicError
from matchgenerator import MatchGenerator
from tournfieldtimescheduler import TournamentFieldTimeScheduler
from tourndbinterface import TournDBInterface
from schedule_util import any_ismore, any_isless
from sched_exporter import ScheduleExporter
from leaguedivprep import getTournamentFieldInfo

class TournamentScheduler:
    def __init__(self, mongoClient, divinfo_col):
        self.tdbInterface = TournDBInterface(mongoClient, divinfo_col)
        self.divinfo_tuple = self.tdbInterface.readDB()
        self.tourn_divinfo = self.divinfo_tuple.dict_list
        self.tindexerGet = self.divinfo_tuple.indexerGet
        self.tfield_tuple = getTournamentFieldInfo()

    def prepGenerate(self):
        totalmatch_list = []
        for division in self.tourn_divinfo:
            nt = division['totalteams']
            team_id_list = self.getTeamID_list(nt)
            nb = division['totalbrackets']
            ne = division['elimination_num']
            div_id = int(division['div_id'])
            if div_id == 2:
                bracket_list=[{'team_id_list': [20, 1, 18], 'bracket_id': 1},
                {'team_id_list': [4, 21, 14], 'bracket_id': 2},
                {'team_id_list': [2, 15, 12], 'bracket_id': 3},
                {'team_id_list': [3, 6, 11], 'bracket_id': 4},
                {'team_id_list': [8, 17, 10], 'bracket_id': 5},
                {'team_id_list': [13, 7, 22], 'bracket_id': 6},
                {'team_id_list': [5, 9, 16, 19], 'bracket_id': 7}]
                '''
                bracket_list = [{'team_id_list':[11, 16, 18, 4],'bracket_id': 1},
                {'team_id_list': [21, 12, 2, 15], 'bracket_id': 2},
                {'team_id_list': [14, 3, 6, 20], 'bracket_id': 3},
                {'team_id_list': [8, 17, 10, 13, 7], 'bracket_id': 4},
                {'team_id_list': [22, 5, 9, 1, 19], 'bracket_id': 5}]
                bracket_list = [{'team_id_list':[11, 1, 18, 4], 'bracket_id':1},
                {'team_id_list':[21, 12, 2, 15],'bracket_id': 2},
                {'team_id_list':[14, 3, 6, 20],'bracket_id': 3},
                {'team_id_list':[8, 17, 10, 13, 7],'bracket_id': 4},
                {'team_id_list':[22, 5, 9, 16, 19],'bracket_id': 5}]
                '''
            else:
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
            match_list = []
            partialgame_list = []
            for bracket in bracket_list:
                # calculate virtual number of game days required as parameter for
                # MatchGenerator object.  Value is equal to #games if #teams is even,
                # if odd, add one to #games.
                numbracket_teams = len(bracket['team_id_list'])
                virtualgamedays = ng if numbracket_teams%2==0 else ng+1
                match = MatchGenerator(numbracket_teams, virtualgamedays, maxGamesPerTeam=ng)
                bracket_match_list = match.generateMatchList(teamid_map=bracket['team_id_list'])
                logging.info("tournscheduler:prepGenerate:div=%d bracket=%s bracketmatch_list=%s",
                             div_id, bracket, bracket_match_list)
                print 'div bracket numgames', div_id, bracket, match.numgames_perteam_list
                if any_isless(match.numgames_perteam_list, ng):
                    index_list = [i for i,j in enumerate(match.numgames_perteam_list) if j < ng]
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
                                    'match_list':match_list, 'max_round':virtualgamedays})
        tourn_ftscheduler = TournamentFieldTimeScheduler(self.tdbInterface,
            self.tfield_tuple,
                                                         self.tourn_divinfo,
                                                         self.tindexerGet)
        tourn_ftscheduler.generateSchedule(totalmatch_list)

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

    def exportSchedule(self):
        tschedExporter = ScheduleExporter(self.tdbInterface.dbInterface,
                                         divinfo_tuple=self.divinfo_tuple,
                                         fieldtuple=self.tfield_tuple)
        '''
        for division in self.tourn_divinfo:
            tschedExporter.exportDivTeamSchedules(div_id=int(division['div_id']),
                                                  age=division['div_age'],
                                                  gen=division['div_gen'],
                                                  numteams=int(division['totalteams']),
                                                  prefix='PHMSACup2013')
            tschedExporter.exportTeamSchedules(div_id=int(division['div_id']),
                                               age=division['div_age'],
                                               gen=division['div_gen'],
                                               numteams=int(division['totalteams']), prefix='PHMSACup2013')
        '''
        tschedExporter.exportFieldScheduleOld(prefix="PHMSACup2013")
            #tschedExporter.exportDivSchedules(division['div_id'])
            #tschedExporter.exportDivSchedulesRefFormat(prefix='PHMSACup')
