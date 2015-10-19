''' Copyright YukonTR 2014 '''
from db.tourndbinterface import TournDBInterface
from db.fielddbinterface import FieldDBInterface
from db.scheddbinterface import SchedDBInterface
from matchgenerator import MatchGenerator
from tournfieldtimescheduler import TournamentFieldTimeScheduleGenerator
from collections import namedtuple
from dateutil import parser
import logging
from html import HTML
from random import shuffle, seed
from math import ceil, log
from util.schedule_util import flatten, roundrobin
from itertools import chain, groupby
from operator import itemgetter
from util.sched_exceptions import CodeLogicError, SchedulerConfigurationError
from pprint import pprint
_logbase2 = lambda x: log(x, 2)
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_List_IndexerGM = namedtuple('List_Indexer', 'dict_list indexerGet indexerMatch')
_List_IndexerM = namedtuple('List_Indexer', 'dict_list indexerMatch')

# Start number for Match ID's (export to UI)
_ELIM_MATCH_ID_START = 100
# Ordering of rounds for winner and losers brackets.  index of order_list
# corresponds to round in respective winner/losers (consolation) bracket
# [0] element of tuple corresponds to winner's bracket, [1] element of
# tuple corresponds to loser's bracket.  Tuple values correspond to absolute
# round id.
DIVCONFIG_INCOMPLETE_MASK = 0x1
FIELDCONFIG_INCOMPLETE_MASK = 0x2
PREFINFODATE_ERROR_MASK = 0x4

DB_TYPE = "tourndb"
IDPROPERTY_str = 'tourndiv_id'
''' main class for launching tournament schedule generator
    Tournament Scheduler supports Elimination-format tournaments:
        - Single Elimination, Double Elimination, Consolation (Modified Double)
    Scheduler also supports generation of 'World Cup'- style tournaments:
        - Round-Robin-format preliminary rounds followed by Elimination rounds
'''
class TournSchedMaster(object):
    def __init__(self, mongoClient, userid_name, divcol_name, fieldcol_name, schedcol_name, tourn_type='RR'):
        self._error_code = 0x0
        self.userid_name = userid_name
        self.sdbInterface = SchedDBInterface(mongoClient, userid_name,
            schedcol_name, "T")
        self.tourn_type = tourn_type
        self.totalmatch_list = list()
        # db_type is for the divinfo schedule attached to the fielddb spec
        dbInterface = TournDBInterface(mongoClient, userid_name, divcol_name, "T")
        dbtuple = dbInterface.readDBraw()
        if dbtuple.config_status == 1:
            self.divinfo_list = dbtuple.list
            self.divinfo_indexerGet = lambda x: dict((p['tourndiv_id'],i) for i,p in enumerate(self.divinfo_list)).get(x)
            self.divinfo_tuple = _List_Indexer(self.divinfo_list,
                self.divinfo_indexerGet)
        else:
            self.divinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schemaster:init: div config not complete=%s" % (divcol_name,))
            self._error_code |= DIVCONFIG_INCOMPLETE_MASK
        # get field information
        fdbInterface = FieldDBInterface(mongoClient, userid_name, fieldcol_name, "T")
        fdbtuple = fdbInterface.readDBraw();
        if fdbtuple.config_status == 1:
            self.fieldinfo_list = fdbtuple.list
            self.fieldinfo_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(self.fieldinfo_list)).get(x)
            self.fieldinfo_tuple = _List_Indexer(self.fieldinfo_list,
                self.fieldinfo_indexerGet)
        else:
            self.fieldinfo_tuple = _List_Indexer(None, None)
            raise CodeLogicError("schedmaster:init: field config not complete=%s" % (fieldcol_name,))
            self._error_code |= FIELDCONFIG_INCOMPLETE_MASK

        # create list of div_ids that do not have a 'divfield_list' key
        divreqfields_list = [x[IDPROPERTY_str] for x in self.divinfo_list if 'divfield_list' not in x]
        # if there are div_id's with no 'divfield_list' key, create it
        if divreqfields_list:
            self.divfield_correlate(self.fieldinfo_list, dbInterface, divreqfields_list)
        else:
            self.simplifydivfield_list()

        if not self._error_code:
            self.sdbInterface.setschedule_param(DB_TYPE, divcol_name, fieldcol_name)
            self.fieldtimeScheduleGenerator = TournamentFieldTimeScheduleGenerator(
                dbinterface=self.sdbInterface, divinfo_tuple=self.divinfo_tuple,
                fieldinfo_tuple=self.fieldinfo_tuple, tourn_type=self.tourn_type)
            self.schedcol_name = schedcol_name
            self._xls_exporter = None

    @property
    def xls_exporter(self):
        return self._xls_exporter

    @xls_exporter.setter
    def xls_exporter(self, value):
        self._xls_exporter = value

    @property
    def error_code(self):
        return self._error_code

    ''' Generate either RoundRobin-format preliminary rounds, or elimination rounds
    '''
    def schedGenerate(self):
        if self.tourn_type == 'RR':
            return self.prepGenerate()
        elif self.tourn_type == 'elimination':
            return self.elimGenerate()

    def get2015_U10_team_ids(self, tourndiv_id, bracket_id):
        bracket_list = [
            {'tourndiv_id': 2,
             'team_ids': [{'team_id_list': [7,9,11,19], 'bracket_id': 2},
                          {'team_id_list': [13,14,6,1], 'bracket_id': 3},
                          {'team_id_list': [3,4,18,17], 'bracket_id': 4},
                          {'team_id_list': [15,16,20,8], 'bracket_id': 5},
                          {'team_id_list': [5,10,12,2], 'bracket_id': 1}]},
            {'tourndiv_id': 1,
             'team_ids': [{'team_id_list': [2,5,9,13,17,21], 'bracket_id': 6},
                          {'team_id_list': [1,4,10,15], 'bracket_id': 5},
                          {'team_id_list': [6,7,14,22], 'bracket_id': 4},
                          {'team_id_list': [3,8,19,26], 'bracket_id': 3},
                          {'team_id_list': [12,25,18,23], 'bracket_id': 2},
                          {'team_id_list': [16,11,20,24], 'bracket_id': 1}]}]
        tindexerGet = lambda x: dict((p['tourndiv_id'],i) for i,p in enumerate(bracket_list)).get(x)
        team_ids = bracket_list[tindexerGet(tourndiv_id)]['team_ids']
        bindexerGet = lambda x: dict((p['bracket_id'],i) for i,p in enumerate(team_ids)).get(x)
        return team_ids[bindexerGet(bracket_id)]['team_id_list']

    def prepGenerate(self):
        totalmatch_list = list()
        for divinfo in self.divinfo_list:
            tourndiv_id = divinfo[IDPROPERTY_str]
            print tourndiv_id
            totalteams = divinfo['totalteams']
            team_list = self.getTeamID_list(totalteams)
            totalgamedays = divinfo['totalgamedays']
            minbracket_size = totalgamedays+1
            brackets_num = totalteams / minbracket_size
            running_index = 0
            #bracket_team_list = list()
            index = 0
            match_list = list()
            for bracket_id in range(1, brackets_num+1):
                if totalteams - (index+minbracket_size) >= minbracket_size:
                    bracket_size = minbracket_size
                else:
                    bracket_size = totalteams - index
                running_index += bracket_size
                if tourndiv_id <= 2:
                    team_id_list = self.get2015_U10_team_ids(tourndiv_id, bracket_id)
                else:
                    team_id_list = team_list[index:running_index]
                if bracket_size != len(team_id_list):
                     raise CodeLogicError('tournschedmaster:bracketsze mismatch div %d bracketsize %d team_id_list %s' % (tourndiv_id, bracket_size, team_id_list))
                # calculate virtual number of game days required as parameter for
                # MatchGenerator object.  Value is equal to #games if #teams is even,
                # if odd, add one to #games.
                vgames_num = totalgamedays if bracket_size%2==0 else totalgamedays+1
                match = MatchGenerator(bracket_size, vgames_num,
                    maxGamesPerTeam=totalgamedays)
                bracket_match_list = match.generateMatchList(
                    teamid_map=team_id_list)
                match_list.append(bracket_match_list)
                #bracket_team_list.append(bracket_dict)
                index = running_index
            totalmatch_list.append({IDPROPERTY_str: divinfo[IDPROPERTY_str],
                'match_list':match_list, 'max_round':vgames_num})
        status = self.fieldtimeScheduleGenerator.generateSchedule(totalmatch_list)
        return 1 if status else 0

    def elimGenerate(self):
        match_id_count = _ELIM_MATCH_ID_START
        totalmatch_list = list()
        for divinfo in self.divinfo_list:
            match_id_begin = match_id_count
            div_name = divinfo['div_age'] + divinfo['div_gen']
            elimination_type = divinfo['elimination_type']
            thirdplace_enable = divinfo['thirdplace_enable']
            # assign bracket type (Winners or Losers)
            btype = 'W'
            totalteams = divinfo['totalteams']
            team_id_list = range(1,totalteams+1)
            # total number of rounds for winner's bracket
            # does not include championship game for double elimination format
            totalwrounds =int(ceil(_logbase2(totalteams)))
            maxpower2 = pow(2, totalwrounds)
            div_id = divinfo[IDPROPERTY_str]
            match_list = []
            divmatch_list = []
            absround_id = 0
            for round_id in range(1, totalwrounds+1):
                absround_id += 1
                if round_id == 1:
                    r1bye_num = maxpower2 - totalteams
                    roundteams_num = totalteams - r1bye_num
                    seed_id_list = team_id_list[-roundteams_num:]
                    rteam_list = ['S'+str(s) for s in seed_id_list]
                    cumulative_list = []
                    cindexerGet = None
                else:
                    roundteams_num = maxpower2/pow(2, round_id-1)
                    seed_id_list = range(1, roundteams_num+1)
                    # rm_list is from previous round, make sure to call this before
                    # rmatch_dict in this round
                    rm_list = rmatch_dict['match_list']
                    rmindexerGet = lambda x: dict((p['next_w_seed'],i) for i,p in enumerate(rm_list)).get(x)
                    # assign team ids to the seeded team list for the current round
                    rteam_list = [rm_list[rmindexerGet(s)]['next_w_id'] if s in carryseed_list else 'S'+str(s) for s in seed_id_list]
                    cumulative_list = [{'match_id':x['match_id'],
                        'cumulative':x['cumulative']} for x in rm_list]
                    cindexerGet = lambda x: dict((p['match_id'],i) for i,p in enumerate(cumulative_list)).get(x)
                    # provide round sequencing information that will be usefol for
                    # fieldtime scheduling
                logging.debug("elimsched:gen:**************")
                logging.debug("elimsched:gen:round %d rteam %s",
                              round_id, rteam_list)
                print 'round rteam', round_id, rteam_list
                # control number to determine pairings is the sum of the highest
                # and lowest seed number of teams playing in round 1
                numgames = roundteams_num/2
                # ref http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
                # for flattening two-deep and regular nested lists
                lseed_list = self.generate_lseed_list(round_id, seed_id_list)
                rmatch_dict = {'round_id': round_id, 'btype':btype,
                    'absround_id': absround_id,
                    'numgames':numgames, 'depend':0, 'div_id':div_id,
                    'match_list': [{'home':rteam_list[x],'away':rteam_list[-x-1],
                        'div_id':div_id,
                        'cumulative':[rteam_list[y] if rteam_list[y][0]=='S' else self.getCumulative_teams(cumulative_list, cindexerGet,rteam_list[y][1:]) for y in (x,-x-1)],
                        'next_w_seed':seed_id_list[x],
                        'next_l_seed':lseed_list[x],
                        'next_w_id':'W'+str(match_id_count+x+1),
                        'next_l_id':'L'+str(match_id_count+x+1),
                        'match_id':match_id_count+x+1,
                        'comment':"", 'round':btype + str(round_id)} for x in range(numgames)
                    ]
                }
                logging.debug("elimsched:gen: div %d round %d",
                              div_id, round_id)
                logging.debug("elimsched:gen: seed list %s lseed %s",
                              seed_id_list, lseed_list)
                for rm in rmatch_dict['match_list']:
                    logging.debug("elimsched:gen: rm %s", rm)
                match_list.append(rmatch_dict)

                # slicing for copying is fastest according to
                # http://stackoverflow.com/questions/2612802/how-to-clone-a-list-in-python/2612810
                carryseed_list = [x['next_w_seed'] for x in rmatch_dict['match_list']]
                match_id_count += len(rmatch_dict['match_list'])
            if elimination_type != 'D':
                # championship game for single and consolation (modified
                # double) elimination tournament - winner of winner's bracket
                # is overall champ.  For double elimination winner of winner's
                # bracket still has to play the winner of the consolaton bracket
                # which is covered below
                rmatch_dict['match_list'][0]['comment'] = div_name + ' Championship Game'
                rmatch_dict['match_list'][0]['round'] = 'Champ'
            divmatch_list.append({'div_id': divinfo[IDPROPERTY_str],
                'elimination_type':elimination_type,
                'btype':btype, 'divmatch_list':match_list,
                'max_round':totalwrounds, 'totalteams':totalteams})
            if totalteams > 2:
                if elimination_type == 'S' and thirdplace_enable == 'Y':
                    # generate third place game for single elimination
                    match_id_count = self.createThirdPlaceMatch(div_id, match_list,
                        totalwrounds, match_id_count, divmatch_list, div_name)
                if elimination_type in ['C', 'D']:
                    (match_id_count, c_absround_id) = self.createConsolationRound(div_id, match_list,totalwrounds, match_id_count, elimination_type, divmatch_list)
                    if elimination_type =='D':
                        # final game for double eliminatio game
                        rm_list = rmatch_dict['match_list']
                        rmindexerGet = lambda x: dict((p['next_w_seed'],i) for i,p in enumerate(rm_list)).get(x)
                        rteam = rm_list[rmindexerGet(carryseed_list[0])]['next_w_id']
                        nextabsround_id = max(rmatch_dict['absround_id'], c_absround_id) + 1
                        rmatch_dict = {'round_id': round_id+1,
                        'absround_id': nextabsround_id, 'btype':btype,
                        'numgames':1, 'depend':0, 'div_id':div_id,
                        'match_list': [{'home':rteam,
                        'away':'W'+str(match_id_count),
                        'div_id':div_id,
                        'match_id':match_id_count+1,
                        'round': 'Champ',
                        'comment':'Championship Game (1st Winner bracket vs 1st place Loser/Repcharge bracket'}]}
                        match_list.append(rmatch_dict)
                        match_id_count += 1
            else:
                logging.warning("elimsched:gen: there should at least be three teams in div %d to make scheduling meaningful", div_id)
            totalmatch_list.append({'div_id':div_id, 'divmatch_list':self.addOverallRoundID(divmatch_list, totalteams, elimination_type),
                'match_id_range':(match_id_begin+1, match_id_count)})
        pprint(totalmatch_list)
        status = self.fieldtimeScheduleGenerator.generateElimSchedule(totalmatch_list)
        #elim_ftscheduler = EliminationFieldTimeScheduler(self.tdbInterface, self.tfield_tuple, self.tourn_divinfo, self.tindexerGet)
        #elim_ftscheduler.generateSchedule(self.totalmatch_list)
        return 1 if status else 0

    def getCumulative_teams(self, clist, cGet, match_id):
        if clist:
            # generator created - watch out for iterating through gen
            return list(flatten(clist[cGet(int(match_id))]
                           ['cumulative']))
        else:
            return None

    def generate_lseed_list(self, round_id, seed_list):
        # create seeding list for losing bracket
        # reverse order of incoming seeding list such that returned list can also
        # be accessed starting index 0 (instead of index -1)
        slen = len(seed_list)
        if slen % 2:
            raise CodeLogicError("elimsched:genlseed: seed list should be even")
        ls_list = seed_list[::-1]
        if round_id % 2 == 0:
            # if round is an even number, then swap adjacent positions -
            # index 0,1 <-> index 1,0; index 2,3 <->index 3,2, etc
            index = 0
            while index < slen:
                ls_list[index], ls_list[index+1] = ls_list[index+1], ls_list[index]
                index += 2
        return ls_list

    def createConsolationRound(self, div_id, match_list, wr_total, match_id_count,
        elimination_type, divmatch_list):
        # create the seed list for the consolation matches by getting
        # the 'losing' seed number from the previous round
        # x in [-1,-2] intended to get last and second-to-last match_list
        # we're assuming wr_total (rounds) has at least 2 rounds (4 teams)
        cmatch_list = []
        cround_id = 1
        rm_list = []
        btype = 'L'
        while True:
            if cround_id == 1:
                wr_round = 2
                # use range if tuple needs to represent range
                cinitindex_tuple = (0,wr_round-1)
                # get info for losing teams from the first two elimination rounds
                # List of tuples - tuple(team id, seed, absround_id)
                ctuple_list = [(y['next_l_id'],y['next_l_seed'],
                    match_list[x]['absround_id'])
                    for x in cinitindex_tuple
                    for y in match_list[x]['match_list']]
                ctuple_list.sort(key=itemgetter(1))
                wr12_losing_teams = len(ctuple_list)
                #min_seed = ctuple_list[0][1]
                logging.debug("elimsched:createConsol: INIT ctuple %s INIT losing teams %d",
                              ctuple_list, wr12_losing_teams)
                # get power of 2 greater than #teams
                cpower2 = pow(2, int(ceil(_logbase2(wr12_losing_teams))))
                c1bye_num = cpower2 - wr12_losing_teams
                nt = wr12_losing_teams - c1bye_num
                seed_id_list = [x[1] for x in ctuple_list[-nt:]]
                rteam_list = [x[0] for x in ctuple_list[-nt:]]
                remain_ctuple_list = ctuple_list[0:-nt]
                # 2-index element of three-tuple x is the absround_id for that
                # team_id's last match
                # calculate the next absround_id, by getting the max of the current
                # absround_id for each team id (designated by W/L of match_id) and
                # adding 1
                nextabsround_id = max([x[2] for x in ctuple_list[-nt:]])+1
                logging.debug("elimsched:createConsol: INIT cpower2 %d cbye %d nt %d seed list %s rteam %s remain %s",
                              cpower2, c1bye_num, nt, seed_id_list, rteam_list,
                              remain_ctuple_list)
                # for cround 1, cumulative list will be made up exclusively from passed match list
                cumulative_list = [{'match_id':y['match_id'],
                    'cumulative':y['cumulative']}
                    for x in cinitindex_tuple for y in match_list[x]['match_list']]
                # save it for use in later rounds
                wr_cumulative_list = cumulative_list[:]
            else:
                rmindexerGet = lambda x: dict((p['next_w_seed'],i) for i,p in enumerate(rm_list)).get(x)
                # for cround 2 and above, cumulative list will at include info from
                # prev cround match list; in addition it may also utiliz match list
                # info from previous wround match lists
                cumulative_list = [{'match_id':x['match_id'],
                    'cumulative':x['cumulative']} for x in rm_list]
                if remain_ctuple_list:
                    cpower2 /= 2
                    if cpower2 == len(remain_ctuple_list):
                        # if an equal number of teams have come in from  the wround
                        # bring the effective number back up
                        cpower2 *= 2
                        wr_round += 1 # for depend dict key
                    remain_seed_list = [x[1] for x in remain_ctuple_list]
                    seed_id_list = carryseed_list + remain_seed_list
                    seed_id_list.sort()
                    rcindexerGet = lambda x: dict((p[1],i) for i,p in enumerate(remain_ctuple_list)).get(x)
                    rteam_list = [rm_list[rmindexerGet(s)]['next_w_id'] if s in carryseed_list else remain_ctuple_list[rcindexerGet(s)][0] for s in seed_id_list]
                    # calculate next absround_id by taking the max out of all
                    # absround_id's attached to effective team_id's feeding into
                    # this round, and then incrementing by one
                    nextabsround_id = max(
                        [nextabsround_id if s in carryseed_list
                        else remain_ctuple_list[rcindexerGet(s)][2]
                        for s in seed_id_list]) + 1
                    remain_ctuple_list = []
                    # adding the whole wround cumu list is overkill, but simple
                    cumulative_list += wr_cumulative_list
                else:
                    # increment incoming source round id from winning bracket
                    wr_round += 1
                    wr_ind = wr_round-1
                    # get default bracket size in current round
                    cpower2 /= 2
                    # get losing team information from current source winner
                    # round
                    if wr_round <= wr_total:
                        ctuple_list = [(y['next_l_id'], y['next_l_seed'],
                            match_list[wr_ind]['absround_id'])
                            for y in match_list[wr_ind]['match_list']]
                        cindexerGet = lambda x: dict((p[1],i) for i,p in enumerate(ctuple_list)).get(x)
                        wr_cumulative_list = [{'match_id':y['match_id'],
                        'cumulative':y['cumulative']}
                        for y in match_list[wr_ind]['match_list']]
                        # get number of incoming teams from winner'sbracket
                        wr_nt = len(ctuple_list)
                        if wr_nt == len(carryseed_list):
                            # bring the default bracket size back up because of increase
                            # in additional games
                            cpower2 *= 2
                            incoming_seed_list = [x[1] for x in ctuple_list]
                            seed_id_list = carryseed_list + incoming_seed_list
                            seed_id_list.sort()
                            rteam_list = [rm_list[rmindexerGet(s)]['next_w_id'] if s in carryseed_list else ctuple_list[cindexerGet(s)][0] for s in seed_id_list]
                            nextabsround_id = max(
                                [nextabsround_id if s in carryseed_list
                                    else ctuple_list[cindexerGet(s)][2]
                                    for s in seed_id_list]) + 1
                            cumulative_list  += wr_cumulative_list
                        elif wr_nt == len(carryseed_list)/2:
                            # if only half the number of games are coming in, save for
                            # the next cround.  For now, implement a round from previous
                            # winners.
                            remain_ctuple_list = ctuple_list[:]
                            seed_id_list = carryseed_list
                            seed_id_list.sort()
                            rteam_list = [rm_list[rmindexerGet(s)]['next_w_id']
                                for s in seed_id_list]
                            nextabsround_id += 1
                            wr_round -= 1 # for depend key used for ordering
                        else:
                            # if there are any other number of teams coming in from the
                            # wround, raise exception.  It might be a legitimate case,
                            # so analyze crash.
                            raise CodeLogicError("elimsched:createConsole: consolation bracket design assumptions not correct div=%d" % (div_id,))
                    else:
                        seed_id_list = carryseed_list
                        seed_id_list.sort()
                        rteam_list = [rm_list[rmindexerGet(s)]['next_w_id']
                            for s in seed_id_list]
                if elimination_type == 'D' and cpower2 == 1:
                    cround_id -= 1   #decrement cround_id to recover last cround
                    break
                nt = cpower2
                logging.debug("elimsched:createConsole: cround %d cpower %d nt %d seed %s rteamlist %s",
                            cround_id, cpower2, nt, seed_id_list, rteam_list)

                logging.debug("elimsched:createConsole: cumu %s", cumulative_list)
            numgames = nt/2
            # get list of cumulative team field for all the match sources that will be used in this round.
            # the match sources for the consolation round will be drawn fro previous consolation rounds and also winner rounds
            # for the first round, the match sources will be drawn from the winning bracket matches

            cindexerGet = lambda x: dict((p['match_id'],i) for i,p in enumerate(cumulative_list)).get(x)
            #self.checkRepeatOpponent(cumulative_list, cindexerGet, rteam_list)
            rmatch_dict = {'round_id': cround_id, 'btype':btype,
                'absround_id': nextabsround_id,
                'numgames':numgames, 'depend':wr_round, 'div_id':div_id,
                'match_list': [{'home':rteam_list[x], 'away':rteam_list[-x-1],
                'div_id':div_id,
                'cumulative':[self.getCumulative_teams(cumulative_list, cindexerGet,rteam_list[y][1:]) for y in (x,-x-1)],
                'next_w_seed':seed_id_list[x],
                'next_l_seed':seed_id_list[-x-1],
                'next_w_id':'W'+str(match_id_count+x+1),
                'next_l_id':'L'+str(match_id_count+x+1),
                'match_id':match_id_count+x+1,
                'comment':"", 'round':btype + str(cround_id)} for x in range(numgames)]}
            logging.debug("elimsched:createConsole&&&&&&&&&&&&&&&&")
            logging.debug("elimsched:createConsole: Consolation div %d round %d",
                          div_id, cround_id)
            for rm in rmatch_dict['match_list']:
                logging.debug("elimsched:createConsole: match %s", rm)
            cmatch_list.append(rmatch_dict)
            rm_list = rmatch_dict['match_list']
            carryseed_list = [x['next_w_seed'] for x in rm_list]
            logging.debug("elimsched.createConsole: carryseed %s", carryseed_list)
            match_id_count += len(rm_list)
            if elimination_type == 'C' and cpower2 == 2:
                rmatch_dict['match_list'][0]['comment'] = "3rd Place Game"
                rmatch_dict['match_list'][0]['round'] = "3rd Place"
                break
            else:
                cround_id += 1
        logging.debug("elimsched:createConsole: div %d consolation sched complete; last match_id = %d", div_id, match_id_count)
        divmatch_list.append({'div_id': div_id,
                            'elimination_type':elimination_type,
                            'btype':btype,
                            'divmatch_list':cmatch_list,
                            'max_round':cround_id})
        # return last absround_id as well as last match_id_count
        return (match_id_count, nextabsround_id)

    def createThirdPlaceMatch(self, div_id, amatch_list, max_round_id,
        match_id_count, divmatch_list, div_name):
        # generate 3rd place match - just take championship match
        # and replace W match_id identifiers with 'L' prefix
        # round_id, absround_id stays the same as the championship match.
        # Only applicable for single elimination matches as third place
        # can be automatically determined for double or consolation tournaments.
        mindexerMatch = lambda x,y:[i for i,p in enumerate(
            amatch_list) if p['div_id']==x and p['round_id']==y]
        mindex = mindexerMatch(div_id, max_round_id)[0]
        rmatch_dict = amatch_list[mindex]
        match_list = rmatch_dict['match_list']
        champ_match = match_list[0]
        third_pl_match = dict()
        third_pl_match['div_id'] = div_id
        third_pl_match['away'] = champ_match['away'].replace('W', 'L')
        third_pl_match['home'] = champ_match['home'].replace('W', 'L')
        third_pl_match['round'] = "3rdPlace"
        third_pl_match['comment'] = div_name + " 3rd Place Match"
        match_id_count += 1
        third_pl_match['match_id'] = match_id_count
        match_list.append(third_pl_match)
        rmatch_dict['numgames'] += 1
        pprint(rmatch_dict)
        return match_id_count

    ''' sort match list according to absround_id
    '''
    def addOverallRoundID(self, adivmatch_list, totalteams, elimination_type):
        adjustedmatch_list = [{'div_id':dkey,
            'divmatch_list':[x['divmatch_list'] for x in ditems]}
            for dkey, ditems in groupby(adivmatch_list,key=itemgetter('div_id'))]
        # adjustedmatch_list should only have one element per div
        # (and there will only be one div, so adjustedmatch_list will be
        # a single element array)
        divmatch_list = adjustedmatch_list[0]['divmatch_list']
        multiplex_match_list = list(roundrobin(divmatch_list))
        return sorted(multiplex_match_list, key=itemgetter('absround_id', 'btype'))

    '''function to add fields key to divinfo_list. Supersedes global function (unnamed) in leaguedivprep'''
    def divfield_correlate(self, fieldinfo_list, dbInterface, div_list):
        # use set to keep track of unique div_id's that have fields attached to them
        divset = set()
        for fieldinfo in fieldinfo_list:
            field_id = fieldinfo['field_id']
            for div_id in fieldinfo['primaryuse_list']:
                if div_id in div_list:
                    index = self.divinfo_indexerGet(div_id)
                    if index is not None:
                        divset.add(div_id)
                        divinfo = self.divinfo_list[index]
                        # check existence of key 'divfield_list' - if it exists, append to list of fields, if not create
                        if 'divfield_list' in divinfo:
                            divinfo['divfield_list'].append(field_id)
                        else:
                            divinfo['divfield_list'] = [field_id]

    def simplifydivfield_list(self):
        ''' create a simplified version of the divfield_list which only
        includes the field_id's - the only value necessary for schedule
        creation; ignore other items such as field name '''
        for divinfo in self.divinfo_list:
            if 'divfield_list' in divinfo:
                new_list = [x['field_id'] for x in divinfo['divfield_list']]
                divinfo['divfield_list'] = new_list

    def get_schedule(self, idproperty, propid, div_age="", div_gen=""):
        if idproperty == 'tourndiv_id':
            divinfo = self.divinfo_list[self.divinfo_indexerGet(propid)]
            game_list = self.sdbInterface.get_schedule(idproperty,
                div_age=divinfo['div_age'], div_gen=divinfo['div_gen'])
            # also get fields info tied to div
            fieldname_dict= {x:self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['field_name'] for x in divinfo['divfield_list']}
            return {'game_list':game_list, 'fieldname_dict':fieldname_dict}
        elif idproperty == 'field_id':
            fieldinfo = self.fieldinfo_list[self.fieldinfo_indexerGet(propid)]
            game_list = self.sdbInterface.get_schedule(idproperty,
                field_id=fieldinfo['field_id'])
            return {'game_list':game_list}
        elif idproperty == 'team_id':
            game_list = self.sdbInterface.get_schedule(idproperty, team_id=propid,
                div_age=div_age, div_gen=div_gen)
            return {'game_list':game_list}
        elif idproperty == 'fair_id':
            # get fairness metrics
            # get divinfo as fairness metric calculations require divinfo
            # parameters
            divinfo = self.divinfo_list[self.divinfo_indexerGet(propid)]
            metrics_list = self.sdbInterface.get_schedule(idproperty,
                div_age=div_age, div_gen=div_gen, divinfo=divinfo,
                fieldinfo_tuple=self.fieldinfo_tuple)
            divfield_list = [{'field_id':x,
                'field_name':self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['field_name']}
                for x in divinfo['divfield_list']]
            return {'metrics_list':metrics_list, 'divfield_list':divfield_list}

    def getTeamID_list(self, teams_num):
        team_id_list = range(1,teams_num+1)
        # ref http://docs.python.org/2/library/random.html#random.shuffle
        # doc above for random shuffle (e.g. for an)
        # start the seed with same number so random functions generates
        # same resuts from run to run/
        seed(0)
        shuffle(team_id_list)
        return team_id_list
