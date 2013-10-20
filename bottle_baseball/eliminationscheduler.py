from dbinterface import MongoDBInterface
from random import shuffle, seed
import logging
from operator import itemgetter
from sched_exceptions import CodeLogicError
from tournfieldtimescheduler import TournamentFieldTimeScheduler
from tourndbinterface import TournDBInterface
from schedule_util import flatten
from sched_exporter import ScheduleExporter
from leaguedivprep import getTournamentFieldInfo
from bisect import bisect_left
from itertools import chain
_power_2s_CONST = [1,2,4,8,16,32,64]
class EliminationScheduler:
    def __init__(self, mongoClient, divinfo_col):
        #self.dbInterface = MongoDBInterface(mongoClient, divinfo_col, rr_type_flag=False)
        self.tdbInterface = TournDBInterface(mongoClient, divinfo_col)
        self.divinfo_tuple = self.tdbInterface.readDB()
        self.tourn_divinfo = self.divinfo_tuple.dict_list
        self.tindexerGet = self.divinfo_tuple.indexerGet
        self.tfield_tuple = getTournamentFieldInfo()

    def generate(self):
        totalmatch_list = []
        match_id_count = 0
        for division in self.tourn_divinfo:
            nt = division['totalteams']
            team_id_list = range(1,nt+1)
            totalrounds = bisect_left(_power_2s_CONST,nt)
            maxpower2 = _power_2s_CONST[totalrounds]
            div_id = division['div_id']
            match_list = []
            for round_id in range(1, totalrounds+1):
                if round_id == 1:
                    r1_byeteams_num = maxpower2 - nt
                    numteams = nt - r1_byeteams_num
                    seed_id_list = team_id_list[-numteams:]
                    rteam_list = ['S'+str(s) for s in seed_id_list]
                    cumulative_list = []
                    cindexerGet = None
                else:
                    numteams = maxpower2/_power_2s_CONST[round_id-1]
                    seed_id_list = range(1,numteams+1)
                    # get difference between current seed list and last
                    # round's seed list
                    highseed_list = list(set(seed_id_list)-set(carryseed_list))
                    # rm_list is from previous round, make sure to call this before
                    # rmatch_dict in this round
                    rm_list = rmatch_dict['match_list']
                    rmindexerGet = lambda x: dict((p['next_w_seed'],i) for i,p in enumerate(rm_list)).get(x)
                    # assign team ids to the seeded team list for the current round
                    rteam_list = [rm_list[rmindexerGet(s)]['next_w_id'] if s in carryseed_list else 'S'+str(s) for s in seed_id_list]
                    cumulative_list = [{'match_id':x['match_id'],
                        'cumulative':x['cumulative']} for x in rm_list]
                    cindexerGet = lambda x: dict((p['match_id'],i) for i,p in enumerate(cumulative_list)).get(x)
                #roundteam_list = [pm_list[x-1] for x in carryseed_list]
                logging.debug("elimsched:gen:**************")
                logging.debug("elimsched:gen:round %d rteam %s",
                              round_id, rteam_list)
                print 'round rteam', round_id, rteam_list
                # control number to determine pairings is the sum of the highest
                # and lowest seed number of teams playing in round 1
                #control_num = r1_list[-1] + r1_list[0]
                numgames = numteams/2
                # ref http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
                # for flattening two-deep and regular nested lists
                rmatch_dict = {'round_id': round_id, 'btype':'W',
                    'numgames':numgames,
                    'match_list': [{'home':rteam_list[x],'away':rteam_list[-x-1],
                    'div_id':div_id,
                    'cumulative':[rteam_list[y] if rteam_list[y][0]=='S' else self.getCumulative_teams(cumulative_list, cindexerGet,rteam_list[y][1:]) for y in (x,-x-1)],
                    'next_w_seed':seed_id_list[x],
                    'next_l_seed':seed_id_list[-x-1],
                    'next_w_id':'W'+str(match_id_count+x+1),
                    'next_l_id':'L'+str(match_id_count+x+1),
                    'match_id':match_id_count+x+1} for x in range(numgames)]}

                logging.debug("elimsched:gen: div %d round %d",
                              div_id, round_id)
                logging.debug("elimsched:gen: seed list %s rmatch %s",
                              seed_id_list, rmatch_dict)
                match_list.append(rmatch_dict)

                # slicing for copying is fastest according to
                # http://stackoverflow.com/questions/2612802/how-to-clone-a-list-in-python/2612810
                carryseed_list = [x['next_w_seed'] for x in rmatch_dict['match_list']]
                match_id_count += len(rmatch_dict['match_list'])
            totalmatch_list.append({'div_id': division['div_id'],
                                    'match_list':match_list,
                                    'max_round':totalrounds})
            if nt > 2:
                self.createConsolationRound(div_id, match_list, totalrounds)
            else:
                logging.warning("elimsched:gen: there should at least be three teams in div %d to make scheduling meaningful", div_id)
        '''
        tourn_ftscheduler = TournamentFieldTimeScheduler(self.tdbInterface, self.tfield_tuple,
                                                         self.tourn_divinfo,
                                                         self.tindexerGet)
        tourn_ftscheduler.generateSchedule(totalmatch_list)
        '''
    def getCumulative_teams(self, cumulative_list, cindexerGet, match_id):
        if cumulative_list:
            return flatten(cumulative_list[cindexerGet(int(match_id))]
                           ['cumulative'])
        else:
            return None

    def createConsolationRound(self, div_id, match_list, wrounds):
        # create the seed list for the consolation matches by getting
        # the 'losing' seed number from the previous round
        # x in [-1,-2] intended to get last and second-to-last match_list
        # we're assuming wrounds has at least 2 rounds (4 teams)
        ctuple_list = [(y['next_l_id'],y['next_l_seed'])
            for x in [0,1] for y in match_list[x]['match_list']]
        ctuple_list.sort(key=itemgetter(1))
        wr12_losing_teams = len(ctuple_list)
        #min_seed = ctuple_list[0][1]
        #ctuple_list = [(x[0],x[1]) for x in ctuple_list]
        logging.debug("elimsched:createConsol: int ctuple %s len %d",
                      ctuple_list, wr12_losing_teams)
        maxpower2 = _power_2s_CONST[bisect_left(_power_2s_CONST, wr12_losing_teams)]
        cbye_num = maxpower2 - wr12_losing_teams
        cr1_num = wr12_losing_teams - cbye_num
        logging.debug("elimsched:createConsol: maxpower2 %d cbye %d cr1 %d",
                      maxpower2, cbye_num, cr1_num)
        cmatch_list = []
        cround_id = 1
        while True:
            if cround_id == 1:
                mround_tuple = (1,2)
                numgames = cr1_num/2
                # get list of cumulative team field for all the match sources that will be used in this round.
                # the match sources for the consolation round will be drawn fro previous consolation rounds and also winner rounds
                # for the first round, the match sources will be drawn from the winning bracket matches
                cumulative_list = [{'match_id':y['match_id'],
                    'cumulative':y['cumulative']}
                    for x in mround_tuple for y in match_list[x]['match_list']]
            cindexerGet = lambda x: dict((p['match_id'],i) for i,p in enumerate(cumulative_list)).get(x)
            rmatch_dict = {'round_id': cround_id, 'btype':'L',
                'numgames':numgames,
                'match_list': [{'home':ctuple_list[x][0], 'away':ctuple_list[-x-1][0],
                'div_id':div_id,
                'cumulative':[self.getCumulative_teams(cumulative_list, cindexerGet,ctuple_list[y][0][1:]) for y in (x,-x-1)],
                'next_w_seed':ctuple_list[x][1],
                'next_l_seed':ctuple_list[-x-1][1],
                'next_w_id':'W'+str(match_id_count+x+1),
                'next_l_id':'L'+str(match_id_count+x+1),
                'match_id':match_id_count+x+1} for x in range(numgames)]}
            logging.debug("elimsched:createConsole&&&&&&&&&&&&&&&&")
            logging.debug("elimsched:createConsole: Consolation div %d round %d",
                          div_id, cround_id)
            logging.debug("elimsched:createConsole: Consolocation rmatch %s",
                          rmatch_dict)
            cmatch_list.append(rmatch_dict)
            cround_id += 1
    def exportSchedule(self):
        tschedExporter = ScheduleExporter(self.tdbInterface.dbInterface,
                                         divinfotuple=self.divinfo_tuple,
                                         fieldtuple=self.tfield_tuple)
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
            tschedExporter.exportDivSchedules(division['div_id'])
            tschedExporter.exportDivSchedulesRefFormat(prefix='PHMSACup')
