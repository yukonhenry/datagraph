from dbinterface import MongoDBInterface
from random import shuffle, seed
import logging
from operator import itemgetter
from sched_exceptions import CodeLogicError
from tournfieldtimescheduler import TournamentFieldTimeScheduler
from tourndbinterface import TournDBInterface
from schedule_util import any_ismore, any_isless
from sched_exporter import ScheduleExporter
from leaguedivprep import getTournamentFieldInfo
from bisect import bisect_left
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
            rmatch_list = []
            for round_id in range(1, totalrounds+1):
                if round_id == 1:
                    r1_byeteams_num = maxpower2 - nt
                    numteams = nt - r1_byeteams_num
                    seed_id_list = team_id_list[-numteams:]
                    rteam_list = ['S'+str(s) for s in seed_id_list]
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
                #roundteam_list = [pm_list[x-1] for x in carryseed_list]
                print '$$$$$$$$$'
                print 'round rteam', round_id, rteam_list
                # control number to determine pairings is the sum of the highest
                # and lowest seed number of teams playing in round 1
                #control_num = r1_list[-1] + r1_list[0]
                numgames = numteams/2
                rmatch_dict = {'round_id': round_id, 'btype':'W',
                    'numgames':numgames,
                    'match_list': [{'home':rteam_list[x],'away':rteam_list[-x-1],
                    'div_id':div_id,
                    'next_w_seed':seed_id_list[x],
                    'next_l_seed':seed_id_list[-x-1],
                    'next_w_id':'W'+str(match_id_count+x+1),
                    'next_l_id':'L'+str(match_id_count+x+1),
                    'match_id':match_id_count+x+1}
                    for x in range(numgames)]}
                print '*************'
                print 'div round', div_id, round_id
                print 'rmatch',rmatch_dict
                print 'seed', seed_id_list
                rmatch_list.append(rmatch_dict)
                if round_id > 1:
                    self.createConsolationRound(rmatch_list)
                # slicing for copying is fastest according to
                # http://stackoverflow.com/questions/2612802/how-to-clone-a-list-in-python/2612810
                carryseed_list = [x['next_w_seed'] for x in rmatch_dict['match_list']]
                match_id_count += len(rmatch_dict['match_list'])
            '''


            totalmatch_list.append({'div_id': division['div_id'],
                                    'match_list':match_list, 'max_round':virtualgamedays})
        tourn_ftscheduler = TournamentFieldTimeScheduler(self.tdbInterface, self.tfield_tuple,
                                                         self.tourn_divinfo,
                                                         self.tindexerGet)
        tourn_ftscheduler.generateSchedule(totalmatch_list)
        '''
    def createConsolationRound(self, match_list):
        mtuple_list = [(y['next_l_id'],y['next_l_seed'])
            for x in [-1,-2] for y in match_list[x]['match_list']]
        mtuple_list.sort(key=itemgetter(1))
        print 'match_tuple', mtuple_list

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
