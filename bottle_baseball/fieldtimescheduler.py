''' Copyright YukonTR 2013 '''
from datetime import  datetime, timedelta
from itertools import cycle, groupby
from schedule_util import roundrobin, all_same, all_value, enum, shift_list, bipartiteMatch
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision, getFieldSeasonStatus_list, getDivFieldEdgeWeight_list, \
     getConnectedDivisions, getLeagueDivInfo, getFieldInfo, getTeamTimeConstraintInfo, getSwapTeamInfo
import logging
from operator import itemgetter
from copy import deepcopy
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, \
     CodeLogicError, SchedulerConfigurationError
from math import ceil, floor
from collections import namedtuple, deque
import networkx as nx
from random import shuffle

start_time_CONST = 'START_TIME'
gameday_id_CONST = 'GAMEDAY_ID'
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
home_CONST = 'HOME'
away_CONST = 'AWAY'
venue_count_CONST = 'VCNT'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
venue_CONST = 'VENUE'
age_CONST = 'AGE'
gen_CONST = 'GEN'
firstslot_CONST = 0
verynegative_CONST = -1e6
verypositive_CONST = 1e6
balanceweight_CONST = 2
time_iteration_max_CONST = 18
field_iteration_max_CONST = 10
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
#http://www.tutorialspoint.com/python/python_classes_objects.htm
class FieldTimeScheduleGenerator:
    def __init__(self, dbinterface):
        leaguediv_tuple = getLeagueDivInfo()
        self.leaguediv = leaguediv_tuple.dict_list
        self.leaguediv_indexerGet = leaguediv_tuple.indexerGet

        field_tuple = getFieldInfo()
        self.fieldinfo = field_tuple.dict_list
        self.fieldinfo_indexerGet = field_tuple.indexerGet

        self.connected_div_components = getConnectedDivisions()
        fstatus_tuple = getFieldSeasonStatus_list()
        self.fieldSeasonStatus = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        #logging.debug("fieldseasonstatus init=%s",self.fieldSeasonStatus)

        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.leaguediv)+1):
            self.total_game_dict[i] = []
        self.dbinterface = dbinterface
        self.current_earlylate_list = []
        self.target_earlylate_list = []
        self.cel_indexerGet = None
        self.tel_indexerGet = None

    def findMinimumCountField(self, homemetrics_list, awaymetrics_list, gd_fieldcount, totalneeded_slots, submin=0):
        # return field_id(s) (can be more than one) that corresponds to the minimum
        # count in the two metrics list.  the minimum should map to the same field in both
        # metric lists, but to take into account cases where field_id with min count is different
        # between two lists, use sum of counts as metric.
        # return field_id(s) - not indices
        #optional parameter submin is used when the submin-th minimum is required, i.e. is submin=1
        #return the 2nd-most minimum count fields
        requiredslots_perfield = int(ceil(float(totalneeded_slots)/len(gd_fieldcount)))
        maxedout_field = None
        almostmaxed_field = None
        maxgd = max(gd_fieldcount, key=itemgetter('count'))
        #for gd in gd_fieldcount:
        diff = maxgd['count'] - requiredslots_perfield
        if diff >= 0:
            #******** cost function
            # 1 is a slack term, arbitrary
            maxedout_field = maxgd['field_id']
            penalty = (diff + 1)*2
        elif diff >= -1:
            almostmaxed_field = maxgd['field_id']
            penalty = diff + 2 # impose additive penalty

        # first ensure both lists are sorted according to field
        # note when calling the sorted function, the list is only shallow-copied.
        # changing a field in the dictionary element in the sorted list also changes the dict
        # in the original list
        # we should make a copy of the list first before sorting
        sorted_homemetrics_list = sorted(homemetrics_list, key=itemgetter('field_id'))
        sorted_awaymetrics_list = sorted(awaymetrics_list, key=itemgetter('field_id'))

        homecount_list = [x['count'] for x in sorted_homemetrics_list]
        awaycount_list = [x['count'] for x in sorted_awaymetrics_list]
        home_field_list = [x['field_id'] for x in sorted_homemetrics_list]
        away_field_list = [x['field_id'] for x in sorted_awaymetrics_list]

        if (set(home_field_list) != set(away_field_list)):
            logging.error("home and away teams have different field lists %s %s",home_field_list, away_field_list)
            raise FieldConsistencyError(home_field_list, away_field_list)
        if maxedout_field:
            maxedout_ind = home_field_list.index(maxedout_field)
            # when scaling, increment by 1 as fieldcount maybe 0
            homecount_list[maxedout_ind] = (homecount_list[maxedout_ind]+1)*penalty
            awaycount_list[maxedout_ind] = (awaycount_list[maxedout_ind]+1)*penalty
            logging.info("ftscheduler:findMinCountField: field=%d maxed out, required=%d ind=%d penalty=%d",
                         maxedout_field, requiredslots_perfield, maxedout_ind, penalty)
            logging.info("ftscheduler:findMinCountField: weighted lists home=%s away=%s",
                         homecount_list, awaycount_list)
        elif almostmaxed_field:
            # if the current field count is almost (one less than) the target count, then incrementally
            # the home/away count list for the field as a penalty - this will incrementally 'slow down'
            # target count from being reached
            almost_ind = home_field_list.index(almostmaxed_field)
            # if count is approaching the limit, give an additive penalty
            homecount_list[almost_ind] += penalty
            awaycount_list[almost_ind] += penalty
            logging.info("ftscheduler:findMinCountField: field=%d Almost Target, required=%d ind=%d",
                         almostmaxed_field, requiredslots_perfield, almost_ind)
            logging.info("ftscheduler:findMinCountField: weighted lists home=%s away=%s",
                         homecount_list, awaycount_list)

       # get min
        sumcount_list = [x+y for (x,y) in zip(homecount_list, awaycount_list)]
        if (submin == 0):
            minsum = min(sumcount_list)
        else:
            try:
                minsum = sorted(sumcount_list)[submin]
            except IndexError:
                logging.error("findMinimumCountField: submin parameter too large %d, needs to be less than %d",
                              submin, len(sumcount_list))
                return None
        # refer to http://stackoverflow.com/questions/3989016/how-to-find-positions-of-the-list-maximum
        minind = [i for i, j in enumerate(sumcount_list) if j == minsum]
        # doesn't matter below if we use home_field_list or away_field_list - should produce same results
        mincount_fields = [home_field_list[i] for i in minind]
        return mincount_fields

    ''' function to increment timeslot counters'''
    def incrementEL_counters(self, homecounter_dict, awaycounter_dict, el_str):
        homecounter_dict[el_str] += 1
        awaycounter_dict[el_str] += 1
        logging.debug("ftscheduler:incrementELcounter: %s h=%s a=%s",
                      el_str, homecounter_dict, awaycounter_dict)

    ''' function to decrement timeslot counters'''
    def decrementEL_counters(self, homecounter_dict, awaycounter_dict, el_str):
        homecounter_dict[el_str] -= 1
        awaycounter_dict[el_str] -= 1
        logging.debug("ftscheduler:decrementELcounter: %s h=%s a=%s",
                      el_str, homecounter_dict, awaycounter_dict)

    def findTeamsDecrementEL_counters(self, field_id, round_id, slot_index, el_str):
        ''' find teams from fieldSeasonStatus list and decrement early/late counters'''
        slotteams = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1][slot_index]['teams']
        slot_div = slotteams['div_id']
        slot_home = slotteams[home_CONST]
        slot_away = slotteams[away_CONST]
        cindex = self.cel_indexerGet(slot_div)
        slot_el_list = self.current_earlylate_list[cindex]['counter_list']
        home_slot_dict = slot_el_list[slot_home-1]
        away_slot_dict = slot_el_list[slot_away-1]
        self.decrementEL_counters(home_slot_dict, away_slot_dict, el_str)

    def getFieldTeamCount(self, tfmetrics, field_id, team_id):
        ''' get field count for team specified - extracted from tfmetrics (teamfieldmetrics extracted by
        div_id from fieldmetrics_list '''
        metrics_list = tfmetrics[team_id-1]
        metrics_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(metrics_list)).get(x)
        count = metrics_list[metrics_indexerGet(field_id)]['count']
        return count

    def getELcost_by_slot(self, slot, teams_dict, last_slot, incoming=0):
        ''' utility function to get early/late metrics given slot index and teams dictionary'''
        if slot == 0 or slot == last_slot:
            # el_measure will indicate desirability of moving away from this time slot
            el_str = 'early' if slot == 0 else 'late'
            fmtuple = self.getELstats(teams_dict, el_str)
            el_measure = fmtuple.measure
        else:
            if incoming == 1:
                # incoming parameter signifies that a cost that will be subtracted from
                #el_measure = verypositive_CONST
                el_measure = 0  # make it a non-factor
            else:
                #el_measure = verynegative_CONST
                el_measure = 0 # same here
        return el_measure

    def FindSwapMatchForTimeBalance(self, div_id, fieldset, diff_groups, el_type, random=0, offset=0):
        ''' find single potential match to swap with; also calculate costs so that optimization
        can be made '''
        diff_str = 'early_diff' if el_type == 'early' else 'late_diff'
        bestswap_list = []
        swap_dict = {}
        for diff_elem in diff_groups:
            # diff groups are sorted according to EL counter differences
            diff_cost = diff_elem[diff_str] # get counter value
            if diff_cost > 0:
                # only work on cases where diff is greater than 0 (needs swapping)
                teams = diff_elem['teams']
                # possibly random shuffle list here
                # http://stackoverflow.com/questions/976882/shuffling-a-list-of-objects-in-python
                for i in range(random):
                    shuffle(teams, lambda:0)  # make it a deterministic shuffle
                for team_id in teams:
                    min_swapmatch_list = []
                    for field_id in fieldset:
                        # games can be on either field
                        fstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list']
                        for gameday_id, fstatus_gameday in enumerate(fstatus, start=1):
                            if fstatus_gameday:
                                # for every field and gameday_id, find game with team_id that falls on EL slot
                                isgame_list = [x['isgame'] for x in fstatus_gameday]
                                lastslot = len(isgame_list)-1-isgame_list[::-1].index(True)
                                slot_index = 0 if el_type == 'early' else lastslot
                                # we are just going to search for matches in the early/late slot
                                match_teams = fstatus_gameday[slot_index]['teams']
                                if match_teams['div_id'] == div_id and \
                                    (match_teams[home_CONST] == team_id or match_teams[away_CONST] == team_id):
                                    # if a match is found, find opponent and it's cost
                                    oppteam_id = match_teams[home_CONST] if match_teams[away_CONST] == team_id else match_teams[away_CONST]
                                    oppteam_cost = self.getSingleTeamELstats(div_id, oppteam_id, el_type)
                                    #print 'found slot 0 match with field=', field_id, 'div=', div_id, 'gameday=', gameday_id, 'team=', team_id, 'opp=', oppteam_id
                                    logging.debug("ftscheduler:FindSwapMatchForTB: found slot0 field=%d div=%d gameday=%d team=%d opp=%d",
                                                  field_id, div_id, gameday_id, team_id, oppteam_id)
                                    # only look for range that does not involve EL slots
                                    swapmatch_list = [{'swapteams':fstatus_gameday[x]['teams'],
                                                       'cost':self.getELstats(fstatus_gameday[x]['teams'], el_type).measure,
                                                       'slot_index':x} for x in range(1,lastslot)]
                                    # ref http://stackoverflow.com/questions/3989016/how-to-find-positions-of-the-list-maximum
                                    if swapmatch_list:
                                        # if potential swaps can be found (sometimes there are only games on EL slots,
                                        # where a swap game won't exist)
                                        min_cost = min(swapmatch_list, key=itemgetter('cost'))['cost']
                                        min_match_index = [i for i, j in enumerate(swapmatch_list) if j['cost'] == min_cost]
                                        # create record that includes all the data
                                        # ********
                                        # including cost function - 'total_cost' below
                                        min_swapmatch_list.append({'swapmatches':[x for i,x in enumerate(swapmatch_list)
                                                                                  if i in min_match_index],
                                                                'min_cost':min_cost, 'gameday_id':gameday_id,
                                                                'field_id':field_id, 'team_id':team_id,
                                                                'oppteam_id':oppteam_id, 'oppteam_cost':oppteam_cost,
                                                                'team_slot':slot_index, 'self_teams':match_teams,
                                                                'total_cost':oppteam_cost-min_cost})
                                    else:
                                        # only one game scheduled on this field this gameday, move on to next day
                                        continue
                    # see sorted description = sort with total_cost first, but with oppteam cost
                    # if necessary
                    if min_swapmatch_list:
                        sorted_min_swapmatch = sorted(min_swapmatch_list,
                                                      key=itemgetter('total_cost', 'oppteam_cost', 'min_cost'),
                                                      reverse=True)
                        # note we can choose to use indices other than 0 for subsequent iterations
                        max_min_swapmatch = sorted_min_swapmatch[0]
                        logging.debug("ftscheduler:findswapmatchtb: swap for div=%d team=%d is=%s",
                                      div_id, team_id, max_min_swapmatch)
                        field_id = max_min_swapmatch['field_id']
                        gameday_id = max_min_swapmatch['gameday_id']
                        ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][gameday_id-1]
                        el_slot_index = max_min_swapmatch['team_slot']
                        el_teams = ftstatus[el_slot_index]['teams']
                        # confirm correctness of team retrieved from ftstatus matches with team retrieved from
                        # max_min_swapmatch structure
                        if el_teams is not max_min_swapmatch['self_teams']:
                            raise CodeLogicError('ftscheduler:findSwapMatchTB:team mismatch %s' % (el_teams,))
                        # get info on swapped match
                        # ref http://stackoverflow.com/questions/9457832/python-list-rotation
                        max_min_deq = deque(max_min_swapmatch['swapmatches'])
                        max_min_deq.rotate(offset)  # return is None, so convert to list in separate statement
                        swapmatches_list = list(max_min_deq)
                        swapmatches_sel = swapmatches_list[0]
                        swap_slot_index = swapmatches_sel['slot_index']

                        swap_teams = ftstatus[swap_slot_index]['teams']
                        if swap_teams is not swapmatches_sel['swapteams']:
                            raise CodeLogicError('ftscheduler:findSwapMatchTB:swap team mismatch %s'%(swapteams,))
                        # do swap
                        ftstatus[el_slot_index]['teams'] = swap_teams
                        ftstatus[swap_slot_index]['teams'] = el_teams
                        lastel_slot = el_slot_index if el_slot_index > 0 else None
                        #print 'lastslot', lastslot, div_id, field_id, gameday_id, el_teams, swap_teams
                        self.updateSlotELCounters(el_slot_index, swap_slot_index, el_teams, swap_teams,
                                                  lastel_slot, None)  # swap slot does not occupy a list lastslot
                        return True
                        #bestswap_list.append(max_min_swapmatch)
        return False
        # work through the swap list
        # and create bgraph graph dictionary structure required by bipartite matching
        # graph created for each field,gameday tuple
        '''
        if bestswap_list:
            for swap in bestswap_list:
                logging.debug("ftscheduler:findswapmatchtb: swap=%s", swap)
                key_tuple = swap['field_id'], swap['gameday_id']
                if key_tuple not in swap_dict:
                    bgraph = {}
                    swap_dict[key_tuple] = bgraph
                else:
                    bgraph = swap_dict.get(key_tuple)
                    if not bgraph:
                        raise CodeLogicError('ftscheduler: a graph should exist')
                tslot = swap['team_slot']
                swapslots = [x['slot_index'] for x in swap['swapteams']]
                if tslot in bgraph:
                    logging.info('ftschedule:findswapmatchtb: graph entry exists for keytuple=%s tslot=%d - check teams',
                                 key_tuple, tslot)
                bgraph[tslot] = swapslots
                logging.debug('ftscheduler:findswapmatchfortb: keytuple=%s graph=%s',
                              key_tuple, bgraph)
        return swap_dict
'''
    def calcELdiff_list(self, div_id):
        tel_index = self.tel_indexerGet(div_id)
        target_el_list = self.target_earlylate_list[tel_index]['target_list']
        cel_index = self.cel_indexerGet(div_id)
        current_el_list = self.current_earlylate_list[cel_index]['counter_list']
        el_diff_list = [{'team_id': i, 'early_diff': x[0]['early']-x[1]['early'], 'late_diff':x[0]['late']-x[1]['late']}
                        for i,x in enumerate(zip(current_el_list, target_el_list), start=1)]
        return el_diff_list

    def calcDivELdiffSum(self, connect_div_list):
        div_eldiff_list = []
        for div_id in connect_div_list:
            el_diff_list = self.calcELdiff_list(div_id)
            div_eldiff_list.append({'div_id':div_id,
                                    'earlydiff_sum':sum(x['early_diff']
                                                        for x in el_diff_list if x['early_diff'] > 0),
                                    'latediff_sum':sum(x['late_diff']
                                                       for x in el_diff_list if x['late_diff'] > 0)})
        return div_eldiff_list

    def swapMatchTimeUpdateEL(self, swap_dict):
        for swap_key in swap_dict:
            field_id = swap_key[0]
            gameday_id = swap_key[1]
            bgraph = swap_dict[swap_key]
            # get last slot information, if it exists (emedded in graph as one of the keys, the other being 0)
            lastslot = None
            for key in bgraph:
                if key > 0:
                    lastslot = key
                    break
            obj = bipartiteMatch(bgraph)
            # obj[0] contains the swap slots in a:b dictionary element - swap slot a w. b
            #print 'field gameday graph swapobj', field_id, gameday_id, bgraph, obj[0]
            ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][gameday_id-1]
            logging.debug("ftscheduler:retimebalance: swap info after bipartite match=%s", obj[0])
            swapteams_dict = obj[0]
            for key_slot in swapteams_dict:
                val_slot = swapteams_dict[key_slot]
                kteams = ftstatus[key_slot]['teams']
                vteams = ftstatus[val_slot]['teams']
                logging.debug("ftscheduler:retimebalance: swapping teams %s at slot %d with teams %s at slot %d",
                              kteams, key_slot, vteams, val_slot)
                ftstatus[val_slot]['teams'] = kteams
                ftstatus[key_slot]['teams'] = vteams
                if key_slot == 0:
                    self.IncDecELCounters(kteams, 'early', increment=False)
                    self.IncDecELCounters(vteams, 'early', increment=True)
                elif lastslot and key_slot == lastslot:
                    self.IncDecELCounters(kteams, 'late', increment=False)
                    self.IncDecELCounters(vteams, 'late', increment=True)

                if val_slot == 0:
                    self.IncDecELCounters(vteams, 'early', increment=False)
                    self.IncDecELCounters(kteams, 'early', increment=True)
                elif lastslot and val_slot == lastslot:
                    self.IncDecELCounters(vteams, 'late', increment=False)
                    self.IncDecELCounters(kteams, 'late', increment=True)

    def getEarlyLateCounterGroups(self, el_diff_list, el_type):
        eldiff_str = 'early_diff' if el_type == 'early' else 'late_diff'
        sorted_list = sorted(el_diff_list, key=itemgetter(eldiff_str), reverse=True)
        logging.debug("ftscheduler:retimebalance: type %s = sorted %s", el_type, sorted_list)
        # ref http://stackoverflow.com/questions/5695208/group-list-by-values for grouping by values
        diff_groups = [{eldiff_str: key, 'teams':[x['team_id'] for x in items]}
                       for key, items in groupby(sorted_list, itemgetter(eldiff_str))]
        logging.debug("ftscheduler:retimebalance: group %s counters %s", el_type, diff_groups)
        return diff_groups


    def ReTimeBalanceELIteration(self, div_set, fieldset, el_type):
        diff_str = 'early_diff' if el_type == 'early' else 'late_diff'
        el_diff_list_list = [self.calcELdiff_list(div_id) for div_id in div_set]
        diff_sum = sum(sum(x[diff_str] for x in el_diff_list if x[diff_str] > 0) for el_diff_list in el_diff_list_list)
        prev_diff_sum = verypositive_CONST
        random_count = 0
        offset_count = 0
        iteration_count = 0
        while diff_sum > 0:
            if diff_sum > prev_diff_sum:
                # if the sum is growing, we need to take corrective action
                random_count += 1
                offset_count += 1
            for el_diff_list, div_id in zip(el_diff_list_list, div_set):
                diff_groups = self.getEarlyLateCounterGroups(el_diff_list, el_type)
                status = self.FindSwapMatchForTimeBalance(div_id, fieldset, diff_groups, el_type,
                                                          random=random_count, offset=offset_count)

            # recalculate EL differences after the swap
            el_diff_list_list = [self.calcELdiff_list(div_id) for div_id in div_set]
            prev_diff_sum = diff_sum
            diff_sum = sum(sum(x[diff_str] for x in el_diff_list if x[diff_str] > 0) for el_diff_list in el_diff_list_list)
            iteration_count += 1
            print 'iteration_count, diffsum', iteration_count, diff_sum
            if iteration_count > time_iteration_max_CONST:
                logging.debug("ftscheduler:retimebalance: div=%s %s time swap exceeds max", div_set, el_type)
                completeflag = False
                break
        else:
            completeflag = True
            logging.debug("ftscheduler:retimebalance: div=%s %s balance achieved", div_set, el_type)
        return completeflag

    def ReTimeBalance(self, fieldset, connected_div_list):
        ''' Rebalance time schedules for teams that have excessive number of early/late games '''
        flag_dict = {}
        for el_type in ['early', 'late']:
            flag_dict[el_type] = False
            for i in range(3):
                estatus = self.ReTimeBalanceELIteration(connected_div_list, fieldset, el_type)
                if estatus:
                    print el_type, 'divset=', connected_div_list, 'time balance SUCCEED'
                    flag_dict[el_type] = True
                    break
            else:
                print el_type, 'divset=', connected_div_list, 'time balance ITERATION MAXED'
        if all(flag_dict.values()):
            return True
        else:
            return False


    def CountFieldBalance(self, connected_div_list, fieldmetrics_list, findexerGet):
        fieldcountdiff_list = []
        for div_id in connected_div_list:
            divinfo = self.leaguediv[self.leaguediv_indexerGet(div_id)]
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            # http://stackoverflow.com/questions/10543303/number-of-values-in-a-list-greater-than-a-certain-number
            fcountdiff_num = sum(max(tmetrics, key=itemgetter('count'))['count']-min(tmetrics, key=itemgetter('count'))['count'] > 1
                                 for tmetrics in tfmetrics)
            fieldcountdiff_list.append({'div_id':div_id, 'fcountdiff_num':fcountdiff_num})
        return fieldcountdiff_list
    def IncDecELCounters(self, teams, el_type, increment):
        ''' inc/dec early/late counters based on el type and inc/dec flag '''
        div_id = teams['div_id']
        home_id = teams[home_CONST]
        away_id = teams[away_CONST]
        cel_index = self.cel_indexerGet(div_id)
        current_el_list = self.current_earlylate_list[cel_index]['counter_list']
        home_currentel_dict = current_el_list[home_id-1]
        away_currentel_dict = current_el_list[away_id-1]
        if increment:
            self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)
        else:
            self.decrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)


    def IncDecFieldMetrics(self, fieldmetrics_list, findexerGet, field_id, teams, increment=True):
        ''' increment/decrement fieldmetrics_list, based on field and team (inc/dec) flag '''
        div_id = teams['div_id']
        home_id = teams[home_CONST]
        away_id = teams[away_CONST]
        tfmetrics_list = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
        home_fieldmetrics_list = tfmetrics_list[home_id-1]
        away_fieldmetrics_list = tfmetrics_list[away_id-1]
        home_fieldmetrics_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list)).get(x)
        away_fieldmetrics_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list)).get(x)
        if increment:
            home_fieldmetrics_list[home_fieldmetrics_indexerGet(field_id)]['count'] += 1
            away_fieldmetrics_list[away_fieldmetrics_indexerGet(field_id)]['count'] += 1
        else:
            home_fieldmetrics_list[home_fieldmetrics_indexerGet(field_id)]['count'] -= 1
            away_fieldmetrics_list[away_fieldmetrics_indexerGet(field_id)]['count'] -= 1

    def ReFieldBalance(self, connected_div_list, fieldmetrics_list, findexerGet):
        rebalance_count = 0
        for div_id in connected_div_list:
            divinfo = self.leaguediv[self.leaguediv_indexerGet(div_id)]
            numgamesperseason = divinfo['gamesperseason']
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            team_id = 1
            for team_metrics in tfmetrics:
                # for each team in the division, get counts for fields with maximum/minimum use counts
                maxuse = max(team_metrics, key=itemgetter('count'))
                minuse = min(team_metrics, key=itemgetter('count'))
                diff = maxuse['count']-minuse['count']
                if diff > 1:
                    # if the difference between max and min is greater than a threshold
                    # (1 in this case)
                    maxfield = maxuse['field_id']
                    minfield = minuse['field_id']
                    #print 'div', div_id, 'team', team_id, 'needs to move from field', maxuse['field_id'], 'to', minuse['field_id'], 'because diff=', diff
                    max_ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(maxfield)]['slotstatus_list']
                    min_ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(minfield)]['slotstatus_list']
                    gameday_id = 1
                    maxfteam_metrics_list = []
                    minfteam_metrics_list = []
                    gameday_totalcost_list = []
                    for max_round_status, min_round_status in zip(max_ftstatus, min_ftstatus):
                        # for each gameday first find game stats for max count fields
                        # for max count fields, find for each gameday, each gameday slot where the target
                        # team plays on the max count field.  Each gameday slot might not involve the
                        # target team because they may be playing on a different field
                        if not max_round_status or not min_round_status:
                            # if max count field is not being used on a particular gameday, skip and go to the next
                            logging.debug("ftscheduler:refieldbalance: either max or min on gameday=%d is None",
                                          gameday_id)
                            gameday_id += 1
                            continue
                        else:
                            logging.debug("continuing on gameday=%d", gameday_id)
                        today_maxfield_info_list = [{'gameday_id':gameday_id, 'slot_index':i,
                                                    'start_time':j['start_time'],
                                                    'teams':j['teams']}
                                                    for i,j in enumerate(max_round_status)
                                                    if j['isgame'] and j['teams']['div_id']==div_id and
                                                    (j['teams'][home_CONST]==team_id or j['teams'][away_CONST]==team_id)]
                        if len(today_maxfield_info_list) > 1:
                            raise CodeLogicError('ftschedule:rebalance: There should only be one game per gameday')
                        if today_maxfield_info_list:
                            logging.info("ftscheduler:refieldbalance: div=%d gameday=%d maxfield=%d minfield=%d",
                                         div_id, gameday_id, maxfield, minfield)
                            today_maxfield_info = today_maxfield_info_list[0]
                            logging.debug("ftscheduler:refieldbalance: maxfield info=%s", today_maxfield_info)
                            # if there is game being played on the max count field by the current team, then first find out
                            # find out how the potential time slot change associated with the field move might affect
                            #early/late time slot counters
                            isgame_list = [x['isgame'] for x in max_round_status]
                            # find 0-index for last game (True) (last game may be in a different division)
                            lastTrue_slot = len(isgame_list)-1-isgame_list[::-1].index(True)
                            maxf_slot = today_maxfield_info['slot_index']
                            el_measure = self.getELcost_by_slot(maxf_slot, today_maxfield_info['teams'], lastTrue_slot)
                            logging.debug('ftscheduler:refieldbalance: maxf_slot=%d el_measure=%d lastslot=%d',
                                          maxf_slot, el_measure, lastTrue_slot)

                            # Next find out who the opponent team is, then find out the field count (for the max count
                            # field) for that opponent team.  We need the count for the opponent because it will affect
                            # it's field count if the game is moved away from the max count field
                            maxf_teams = today_maxfield_info['teams']
                            oppteam_id = maxf_teams[home_CONST] if maxf_teams[away_CONST]==team_id else maxf_teams[away_CONST]
                            maxfield_opp_count = self.getFieldTeamCount(tfmetrics, maxfield, oppteam_id)
                            minfield_opp_count = self.getFieldTeamCount(tfmetrics, minfield, oppteam_id)
                            # the measure for opponent team - desirability to swap out this game - is just the difference
                            # between max and min field counts
                            opp_measure = maxfield_opp_count - minfield_opp_count
                            # *****
                            # Calculate Total cost for swapping out the maxfield game (with the designated team_id) in the
                            # current gameday.
                            # total cost = early/late swap out measure (if slot is 0 or last) +
                            # opponent team max min field count diff (opp_measure) +
                            # we might want to scale the opp_measure over the el_measure as we are focused on field
                            # balacning - leave equal weight for now
                            maxftotal_cost = el_measure + balanceweight_CONST*opp_measure
                            # summarize all the info and metrics for the swapped-out game from the max count field
                            # maxfteam_metrics_list persists outside of this current gameday and is used to choose the
                            # best match involving the maxfteam out of all the gamedays to swap out
                            maxfteam_metrics = {'team':team_id, 'oppteam_id':oppteam_id, 'maxf_count':maxfield_opp_count,
                                                'minf_count':minfield_opp_count, 'opp_measure':opp_measure,
                                                'gameday_id':gameday_id, 'el_measure':el_measure,
                                                'maxftotal_cost':maxftotal_cost}
                            maxfteam_metrics_list.append(maxfteam_metrics)
                            logging.debug('ftscheduler:refieldbalance: maxfield team metrics=%s', maxfteam_metrics)
                            # Now we are going to find all the teams (not just in this div but also all field-shared divs)
                            # using the minimum count field
                            # and then find the measures for each field - which is both the minfield counts for the home and
                            # away teams, along with the timeslot early/late count - el count only generated if the slot index
                            # falls under the 0 or last slot
                            # move some fields to general for loop as list comprehension gets too messy.
                            today_minfield_info = [{'slot_index':i, 'teams':j['teams']}
                                                   for i,j in enumerate(min_round_status) if j['isgame']]
                            minf_isgame_list = [x['isgame'] for x in min_round_status]
                            # find 0-index for last game (True) (last game may be in a different division)
                            minf_lastTrue_slot = len(minf_isgame_list)-1-minf_isgame_list[::-1].index(True)
                            for minfo in today_minfield_info:
                                mteams = minfo['teams']
                                mhome = mteams[home_CONST]
                                maway = mteams[away_CONST]
                                mtfmetrics = fieldmetrics_list[findexerGet(mteams['div_id'])]['tfmetrics']
                                minfo['homeminf_count'] = self.getFieldTeamCount(mtfmetrics, minfield, mhome)
                                minfo['homemaxf_count'] = self.getFieldTeamCount(mtfmetrics, maxfield, mhome)
                                minfo['awayminf_count'] = self.getFieldTeamCount(mtfmetrics, minfield, maway)
                                minfo['awaymaxf_count'] = self.getFieldTeamCount(mtfmetrics, maxfield, maway)
                                slot = minfo['slot_index']
                                # get cost associated with early/late counters, if any (0 val if not)
                                minfo['el_cost'] = self.getELcost_by_slot(slot, mteams, minf_lastTrue_slot)
                                # also get el counters for maxfield teams - they might be swapped into an el slot
                                minfo['maxfteams_in_cost'] = self.getELcost_by_slot(slot, maxf_teams,
                                                                                    minf_lastTrue_slot, incoming=1)
                                # get the cost for the min field teams to swap into the max field slot (incoming)
                                # relevant when the maxfield slot is an early/late slot
                                # note lastTrue_slot is for maxfield
                                minfo['maxfslot_el_cost'] = self.getELcost_by_slot(maxf_slot, mteams,
                                                                                   lastTrue_slot, incoming=1)
                                # calculate min field teams to swap out from the min field slot to max field slot
                                homeswap_cost = minfo['homeminf_count']-minfo['homemaxf_count']
                                awayswap_cost = minfo['awayminf_count']-minfo['awaymaxf_count']
                                minfo['fieldswap_cost'] = homeswap_cost + awayswap_cost
                                #***********
                                # Total cost for swapping out minfield matches is the sum of
                                # swap out cost for minfield matches + early/late cost for min field match -
                                # cost for maxf teams to come into the min field slot -
                                # cost for minfield teams to go into max field slot
                                minfo['totalswap_cost'] = balanceweight_CONST*minfo['fieldswap_cost'] + minfo['el_cost'] \
                                  - balanceweight_CONST*minfo['maxfteams_in_cost'] - minfo['maxfslot_el_cost']
                            sorted_minfield_info = sorted(today_minfield_info, key=itemgetter('totalswap_cost'), reverse=True)
                            max_minfo = max(today_minfield_info, key=itemgetter('totalswap_cost'))
                            max_minfo['gameday_id'] = gameday_id
                            minfteam_metrics_list.append(max_minfo)
                            gameday_totalcost = {'gameday_id':gameday_id, 'maxf_slot':maxf_slot, 'oppteam_id':oppteam_id,
                                                 'minf_slot':max_minfo['slot_index'], 'minf_teams':max_minfo['teams'],
                                                 'minf_lastTrue_slot':minf_lastTrue_slot, 'maxf_lastTrue_slot':lastTrue_slot,
                                                  'total_cost':max_minfo['totalswap_cost']+maxfteam_metrics['maxftotal_cost']}
                            gameday_totalcost_list.append(gameday_totalcost)
                            #logging.debug('ftscheduler:refieldbalance: minfield_info=%s', today_minfield_info)
                            #logging.debug('ftscheduler:refieldbalance: sorted minfield=%s', today_minfield_info)
                            logging.debug('ftscheduler:refieldbalance: max minfield=%s', max_minfo)
                            logging.debug('ftscheduler:refieldbalance: totalcost=%s', gameday_totalcost)
                        gameday_id += 1
                    # ******
                    # maximize cost by just taking max of total_cost on list
                    max_totalcost = max(gameday_totalcost_list, key=itemgetter('total_cost'))
                    max_gameday_id = max_totalcost['gameday_id']
                    max_oppteam_id = max_totalcost['oppteam_id']
                    max_maxf_slot = max_totalcost['maxf_slot']
                    max_minf_teams = max_totalcost['minf_teams']
                    max_minf_div_id = max_minf_teams['div_id']
                    max_minf_home_id = max_minf_teams[home_CONST]
                    max_minf_away_id = max_minf_teams[away_CONST]
                    max_minf_slot = max_totalcost['minf_slot']
                    max_minf_lastTrue_slot = max_totalcost['minf_lastTrue_slot']
                    max_maxf_lastTrue_slot = max_totalcost['maxf_lastTrue_slot']
                    logging.debug('ftscheduler:refieldbalance: totalcost_list=%s', gameday_totalcost_list)
                    logging.debug('ftscheduler:refieldbalance: maximum cost info=%s', max_totalcost)

                    logging.debug('ftscheduler:refieldbalance: swapping div=%d team=%d playing oppoent=%d on gameday=%d, slot=%d field=%d',
                                  div_id, team_id, max_oppteam_id, max_gameday_id, max_maxf_slot, maxfield)
                    logging.debug('ftscheduler:refieldbalance: swap with match div=%d, home=%d away=%d, slot=%d field=%d',
                                  max_minf_div_id, max_minf_home_id, max_minf_away_id, max_minf_slot, minfield)
                    # ready to swap matches
                    maxf_teams = max_ftstatus[max_gameday_id-1][max_maxf_slot]['teams']
                    minf_teams = min_ftstatus[max_gameday_id-1][max_minf_slot]['teams']
                    logging.debug('teams check only before swap maxf=%s minf=%s', max_ftstatus[max_gameday_id-1][max_maxf_slot],
                                  min_ftstatus[max_gameday_id-1][max_minf_slot])
                    max_ftstatus[max_gameday_id-1][max_maxf_slot]['teams'] = minf_teams
                    min_ftstatus[max_gameday_id-1][max_minf_slot]['teams'] = maxf_teams
                    logging.debug('teams check only after swap maxf=%s minf=%s', max_ftstatus[max_gameday_id-1][max_maxf_slot],
                                  min_ftstatus[max_gameday_id-1][max_minf_slot])
                    # increment/decrement fieldmetrics
                    # maxf teams moves out of maxfield, so decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, maxfield, maxf_teams,
                                            increment=False)
                    # maxf teams moves into minfield, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, minfield, maxf_teams,
                                            increment=True)
                    # minf teams moves out of minfield, decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, minfield, minf_teams,
                                            increment=False)
                    # minf teams moves into maxfield, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, maxfield, minf_teams,
                                            increment=True)
                    # next adjust EL counters for maxf and minfteams
                    self.updateSlotELCounters(max_maxf_slot, max_minf_slot, maxf_teams, minf_teams,
                                              lastTrue_slot1 = max_maxf_lastTrue_slot,
                                              lastTrue_slot2 = max_minf_lastTrue_slot)
                team_id += 1
        return rebalance_count

    def updateSlotELCounters(self, slot1, slot2, origslot1_teams, origslot2_teams,
                             lastTrue_slot1 = None, lastTrue_slot2 = None):
        if slot1 == 0:
            self.IncDecELCounters(origslot1_teams, 'early', increment=False)
            self.IncDecELCounters(origslot2_teams, 'early', increment=True)
        elif lastTrue_slot1 and slot1 == lastTrue_slot1:
            self.IncDecELCounters(origslot1_teams, 'late', increment=False)
            self.IncDecELCounters(origslot2_teams, 'late', increment=True)

        if slot2 == 0:
            self.IncDecELCounters(origslot2_teams, 'early', increment=False)
            self.IncDecELCounters(origslot1_teams, 'early', increment=True)
        elif lastTrue_slot2 and slot2 == lastTrue_slot2:
            self.IncDecELCounters(origslot2_teams, 'late', increment=False)
            self.IncDecELCounters(origslot1_teams, 'late', increment=True)


    def shiftFSstatus_list(self, field_id, round_id, first_pos):
        ''' shift self.fieldSeasonStatus struct for a given field and gameday_id when a new match
        is scheduled for slot 0 '''
        # ref http://stackoverflow.com/questions/522372/finding-first-and-last-index-of-some-value-in-a-list-in-python
        gameday_list = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1]
        isgame_list = [x['isgame'] for x in gameday_list]
        #firstTrue = isgame_list.index(True)
        #if firstTrue != 0:
        #    return False
        # check to make sure that the first slot to shift has a game scheduled
        if not isgame_list[first_pos]:
            logging.error("ftscheduler:shiftFSstatus: field=%d round=%d status shows slot=%d has no game",
                          field_id, round_id, first_pos)
            return False
        # see above reference for getting last index of a specified value in a list
        lastTrue = len(isgame_list)-1-isgame_list[::-1].index(True)
        index = lastTrue
        shiftcount = 0
        while index >= first_pos:
            gameday_list[index+1]['isgame'] = gameday_list[index]['isgame']
            # reference copy of dict should be sufficient below, but need to confirm
            gameday_list[index+1]['teams'] = gameday_list[index]['teams']
            index -= 1
            shiftcount += 1
        gameday_list[first_pos]['isgame'] = False
        gameday_list[first_pos]['teams'] = {}
        return shiftcount

    def compareCounterToTarget(self, match_list, el_str):
        rflag = False
        fs_list = []
        for field_match in match_list:
            match = field_match['match']
            fmtuple = self.getELstats(match, el_str)
            home_el_dict = fmtuple.home_el_dict
            away_el_dict = fmtuple.away_el_dict
            home_el = home_el_dict[el_str]
            away_el = away_el_dict[el_str]

            home_el_target = fmtuple.home_target_dict[el_str]
            away_el_target = fmtuple.away_target_dict[el_str]

            measure = home_el-home_el_target + away_el-away_el_target
#            if measure > 0:
            if (home_el > home_el_target and away_el > away_el_target):
                # if the current home and away early counts are both greater than
                # the target amount, they can afford to be bumped out the earliest
                # slots; current match will take its place at slot 0
                fs_list.append({'field_id':field_match['field_id'], 'slot_index':field_match['newslot'],
                                'home_el':home_el_dict, 'away_el':away_el_dict,
                                'measure':measure})
                rflag = True
        if rflag:
            best_slot = max(fs_list, key=itemgetter('measure'))
            field_id = best_slot['field_id']
            slot_index = best_slot['slot_index']
            # decrement counters for teams whose match will lose earliest or latest slot
            self.decrementEL_counters(best_slot['home_el'], best_slot['away_el'], el_str)
            FieldSlotTuple = namedtuple('FieldSlotTuple', 'field_id slot_index')
            return FieldSlotTuple(field_id, slot_index)
        else:
            return None

    def getSingleTeamELstats(self, div_id, team_id, el_str):
        ''' utility method to extract home,away teams, and their respective current and
        target counters'''
        # find early late counters for home/away teams
        cel_index = self.cel_indexerGet(div_id)
        cel_list = self.current_earlylate_list[cel_index]['counter_list']
        el_dict = cel_list[team_id-1]

        # also find out target early/late count values
        tel_index = self.tel_indexerGet(div_id)
        tel_list = self.target_earlylate_list[tel_index]['target_list']
        target_dict = tel_list[team_id-1]

        el_count = el_dict[el_str]
        el_target = target_dict[el_str]

        measure = el_count - el_target
        return measure

    def getELstats(self, match, el_str):
        ''' utility method to extract home,away teams, and their respective current and
        target counters'''
        did = match['div_id']
        home_ind = match[home_CONST]-1  # list index index so subtract 1
        away_ind = match[away_CONST]-1
        # find early late counters for home/away teams
        cel_index = self.cel_indexerGet(did)
        cel_list = self.current_earlylate_list[cel_index]['counter_list']
        home_el_dict = cel_list[home_ind]
        away_el_dict = cel_list[away_ind]

        # also find out target early/late count values
        tel_index = self.tel_indexerGet(did)
        tel_list = self.target_earlylate_list[tel_index]['target_list']
        home_target_dict = tel_list[home_ind]
        away_target_dict = tel_list[away_ind]

        home_el = home_el_dict[el_str]
        away_el = away_el_dict[el_str]
        home_el_target = home_target_dict[el_str]
        away_el_target = away_target_dict[el_str]

        measure = home_el-home_el_target + away_el-away_el_target

        ELstats_tuple = namedtuple('ELstats_tuple',
                                   'home_el_dict away_el_dict home_target_dict away_target_dict measure')

        return ELstats_tuple(home_el_dict, away_el_dict, home_target_dict, away_target_dict, measure)

    def findBestSlot(self, match_list):
        ''' find best selection of field/slot index given by match_list parameter.  Optimal choice is selected
        by finding max of 'measure' - initially defined to be the sum of the differences of home and away counts
        compared to target.  This function is created so that even when EL_enum state is 'normal', and optimal
        choice can be made to insert at either the beginning or end of the gameday schedule.  Created to
        provided flexibility when total or per-team div early/late counts have met their targets '''

        rflag = False
        fs_list = []
        for field_match in match_list:
            field_id = field_match['field_id']
            # zip is used in for loop because we assume that early and late counters are relevant
            # to first and last matches (respectively) exclusively.
            # see calling function for how newslot paramenters are assigned.
            for (matchtype, el_str, slotind) in zip(['firstmatch', 'lastmatch'],
                                                    ['early', 'late'],
                                                    ['firstmatch_newslot', 'lastmatch_newslot']):
                match = field_match[matchtype]
                fmtuple = self.getELstats(match, el_str)
                home_el_dict = fmtuple.home_el_dict
                away_el_dict = fmtuple.away_el_dict
                measure = fmtuple.measure
                if measure > 1:
                    fs_list.append({'field_id':field_id, 'slot_index':field_match[slotind],
                                    'home_el_dict':home_el_dict, 'away_el_dict':away_el_dict,
                                    'el_str':el_str, 'measure':measure})
                    rflag = True
        if rflag:
            best_slot = max(fs_list, key=itemgetter('measure'))
            field_id = best_slot['field_id']
            slot_index = best_slot['slot_index']
            el_str = best_slot['el_str']
            # decrement counters for teams whose match will lose earliest or latest slot
            self.decrementEL_counters(best_slot['home_el_dict'], best_slot['away_el_dict'], el_str)
            FieldSlotELType_tuple = namedtuple('FieldSlotELType_tuple', 'field_id slot_index el_str')
            return FieldSlotELType_tuple(field_id, slot_index, el_str)
        else:
            return None

    def generateSchedule(self, total_match_list):
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in total_match_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        # indexer below is used to protect against list of dictionaries that are not ordered according to id,
        # though it is a protective measure, as the list should be ordered with the id.
        match_list_indexer = dict((p['div_id'],i) for i,p in enumerate(total_match_list))
        self.dbinterface.resetSchedStatus_col()
        self.dbinterface.dropGameCollection()  # reset game schedule collection

        # used for calaculating time balancing metrics
        ew_list_indexer = getDivFieldEdgeWeight_list()
        #enum defined in sched_util.py
        EL_enum = enum(NORMAL=0x0, EARLY_DIVTOTAL_NOTMET=0x1, LATE_DIVTOTAL_NOTMET=0x2,
                       EARLY_TEAM_NOTMET=0x4, LATE_TEAM_NOTMET=0x8)

        # work with each set of connected divisions w. shared field
        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            submatch_list = []
            gameinterval_dict = {}
            # note following counters can be initialized within the connected_div_components
            # loop because the divisions are completely isolated from each other
            # outside of the inner div_id/connected_div_list loop below
            targetfieldcount_list = []
            fieldmetrics_list = []
            max_submatchrounds = 0
            divtotal_el_list = []
            # take one of those connected divisions and iterate through each division
            for div_id in connected_div_list:
                divindex = self.leaguediv_indexerGet(div_id)
                divinfo = self.leaguediv[divindex]
                divfields = divinfo['fields']
                numteams = divinfo['totalteams']
                fset.update(divfields)  #incremental union to set of shareable fields
                # http://docs.python.org/2/library/datetime.html#timedelta-objects
                # see also python-in-nutshell
                # convert gameinterval into datetime.timedelta object
                ginterval = divinfo['gameinterval']
                gameinterval_dict[div_id] = timedelta(0,0,0,0,ginterval)
                # get match list for indexed division
                divmatch_dict = total_match_list[match_list_indexer.get(div_id)]
                submatch_list.append(divmatch_dict)
                # calculate number of rounds (gameslots) for the division, and update max if it is the largest
                # amongst connected divisions
                submatchrounds = len(divmatch_dict['match_list'])
                if submatchrounds > max_submatchrounds:
                    max_submatchrounds = submatchrounds
                # describe target fair field usage cout
                numdivfields = len(divfields)
                # get number of games scheduled for each team in dvision
                numgames_list = divmatch_dict['numgames_list']
                logging.debug("divsion=%d numgames_list=%s",div_id,numgames_list)
                # for each team, number of games targeted for each field.
                # similar to homeaway balancing number can be scalar (if #teams/#fields is mod 0)
                # or it can be a two element range (floor(#teams/#fields), same floor+1)
                # the target number of games per fields is the same for each field
                numgamesperfield_list = [[n/numdivfields]
                                         if n%numdivfields==0 else [n/numdivfields,n/numdivfields+1]
                                         for n in numgames_list]
                targetfieldcount_list.append({'div_id':div_id, 'targetperfield':numgamesperfield_list})

                fmetrics_list = [{'field_id':x, 'count':0} for x in divfields]
                # note below numteams*[fmetrics_list] only does a shallow copy; use deepcopy
                tfmetrics_list = [deepcopy(fmetrics_list) for i in range(numteams)]
                fieldmetrics_list.append({'div_id':div_id, 'tfmetrics':tfmetrics_list})
                # metrics and counters for time balancing:
                numgamesperseason = divinfo['gamesperseason']
                # expected total fair share of number of early OR late games for each division
                # eff_edgeweight represents 'fair share' of fields
                # factor of 2 comes in because each time slots gets credited to two teams
                # (home and away)
                ew_list = ew_list_indexer.dict_list
                ew_indexerGet = ew_list_indexer.indexerGet
                divtarget_el = 2*numgamesperseason*ew_list[ew_indexerGet(div_id)]['prodratio']
                # per team fair share of early or late time slots
                teamtarget_el = int(ceil(divtarget_el/numteams))  # float value
                # calculate each team's target share of early and late games
                earlylate_list = [{'early':teamtarget_el, 'late':teamtarget_el} for i in range(numteams)]
                self.target_earlylate_list.append({'div_id':div_id, 'target_list':earlylate_list})
                # each division's target share of early and late games
                # we have this metric because we are using 'ceil' for the team target so not every team
                # will have to meet requirements
                # Changed, 8/2/13 to 'round' - as round better preserves the divtotal requirements for the
                # connected divisions group.
                # we want #numdivision*gamesperseason*2*totalnumfield_in_connected_div
                # factor 2 above is due to double credit because each game involves two teams
                divtotal_el_list.append({'div_id':div_id, 'early':int(round(divtarget_el)),
                                                'late':int(round(divtarget_el))})
                #initialize early late slot counter
                counter_list = [{'early':0, 'late':0} for i in range(numteams)]
                self.current_earlylate_list.append({'div_id':div_id, 'counter_list':counter_list})
            logging.debug('ftscheduler: target num games per fields=%s',targetfieldcount_list)
            logging.debug('ftscheduler: target early late games=%s divtotal target=%s',
                          self.target_earlylate_list, divtotal_el_list)
            # we are assuming still below that all fields in fset are shared by the field-sharing
            # divisions, i.e. we are not sufficiently handing cases where div1 uses fields [1,2]
            # and div2 is using fields[2,3] (field 2 is shared but not 1 and 3)

            fieldmetrics_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(fieldmetrics_list)).get(x)
            targetfieldcount_indexer = dict((p['div_id'],i) for i,p in enumerate(targetfieldcount_list))
            divtotalel_indexer =  dict((p['div_id'],i) for i,p in enumerate(divtotal_el_list))
            self.cel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.current_earlylate_list)).get(x)
            self.tel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.target_earlylate_list)).get(x)

            # use generator list comprehenshion to calcuate sum of required and available fieldslots
            # http://www.python.org/dev/peps/pep-0289/
            required_gameslotsperday = sum(total_match_list[match_list_indexer.get(d)]['gameslotsperday']
                                           for d in connected_div_list)
            available_gameslotsperday = sum(self.fieldSeasonStatus[self.fstatus_indexerGet(f)]['gameslotsperday'] for f in fset)
            logging.debug("for divs=%s fset=%s required slots=%d available=%d",
                          connected_div_list, fset, required_gameslotsperday, available_gameslotsperday)
            if available_gameslotsperday < required_gameslotsperday:
                logging.error("!!!!!!!!!!!!!!!!")
                logging.error("Not enough game slots, need %d slots, but only %d available",
                              required_gameslotsperday, available_gameslotsperday)
                logging.error("!!!!Either add more time slots or fields!!!")
                raise FieldTimeAvailabilityError(connected_div_list)
            for round_id in range(1,max_submatchrounds+1):
                # counters below count how many time each field is used for every gameday
                # reset for each round/gameday
                gameday_fieldcount = [{'field_id':y, 'count':0} for y in fset]
                gd_fieldcount_indexerGet =  lambda x: dict((p['field_id'],i) for i,p in enumerate(gameday_fieldcount)).get(x)
                # create combined list of matches so that it can be passed to the multiplexing
                # function 'roundrobin' below
                combined_match_list = []
                for div_dict in submatch_list:
                    divmatch_list = div_dict['match_list']
                    matchlist_indexer = dict((p[round_id_CONST],i) for i,p in enumerate(divmatch_list))
                    rindex = matchlist_indexer.get(round_id)
                    if rindex is not None:
                        div_id = div_dict['div_id']
                        match_list = divmatch_list[rindex]
                        game_list = match_list[game_team_CONST]
                        round_match_list = []
                        for game in game_list:
                            round_match_list.append({'div_id':div_id, 'game':game, 'round_id':round_id,
                                                     'gameinterval':gameinterval_dict[div_id]})
                        combined_match_list.append(round_match_list)
                    else:
                        continue  # skip over this division if it has run out of gameslots

                # mutliplex the divisions that are sharing fields; user itertools round robin utility
                #http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
                # http://stackoverflow.com/questions/7529376/pythonic-way-to-mix-two-lists
                rrgenobj = roundrobin(combined_match_list)
                for rrgame in rrgenobj:
                    div_id = rrgame['div_id']
                    dindex = fieldmetrics_indexerGet(div_id)
                    teamfieldmetrics_list = fieldmetrics_list[dindex]['tfmetrics']

                    gameinfo = rrgame['game']
                    home_id = gameinfo[home_CONST]
                    away_id = gameinfo[away_CONST]

                    home_fieldmetrics_list = teamfieldmetrics_list[home_id-1]
                    away_fieldmetrics_list = teamfieldmetrics_list[away_id-1]

                    tel_index = self.tel_indexerGet(div_id)
                    target_el_list = self.target_earlylate_list[tel_index]['target_list']
                    home_targetel_dict = target_el_list[home_id-1]
                    away_targetel_dict = target_el_list[away_id-1]
                    cel_index = self.cel_indexerGet(div_id)
                    current_el_list = self.current_earlylate_list[cel_index]['counter_list']
                    home_currentel_dict = current_el_list[home_id-1]
                    away_currentel_dict = current_el_list[away_id-1]

                    divtotal_el_dict = divtotal_el_list[divtotalel_indexer.get(div_id)]
                    divearly_count = sum(current_el_list[x]['early'] for x in range(len(current_el_list)))
                    divlate_count = sum(current_el_list[x]['late'] for x in range(len(current_el_list)))
                    el_state = EL_enum.NORMAL
                    if (divearly_count < divtotal_el_dict['early']):
                        el_state |= EL_enum.EARLY_DIVTOTAL_NOTMET
                    if (divlate_count < divtotal_el_dict['late']):
                        el_state |= EL_enum.LATE_DIVTOTAL_NOTMET
                    if (home_currentel_dict['early'] < home_targetel_dict['early'] and
                        away_currentel_dict['early'] < away_targetel_dict['early']):
                        el_state |= EL_enum.EARLY_TEAM_NOTMET
                    if (home_currentel_dict['late'] < home_targetel_dict['late'] and
                          away_currentel_dict['late'] < away_targetel_dict['late']):
                        el_state |= EL_enum.LATE_TEAM_NOTMET

                    logging.debug("----------------------")
                    logging.debug("fieldtimescheduler: rrgenobj loop div=%d round_id=%d home=%d away=%d",
                                  div_id, round_id, home_id, away_id)
                    logging.debug("early late hometarget=%s awaytarget=%s homecurrent=%s awaycurrent=%s",
                                  home_targetel_dict, away_targetel_dict, home_currentel_dict, away_currentel_dict)
                    submin = 0
                    while True:
                        # first find fields based strictly on field balancing criteria
                        fieldcand_list = self.findMinimumCountField(home_fieldmetrics_list, away_fieldmetrics_list,
                                                                    gameday_fieldcount, required_gameslotsperday, submin)
                        if not fieldcand_list:
                            raise FieldAvailabilityError(div_id)
                        logging.debug("rrgenobj while True loop:")
                        logging.debug("divid=%d round_id=%d home=%d away=%d homemetrics=%s awaymetrics=%s mincount fields=%s",
                                      div_id, round_id, home_id, away_id, home_fieldmetrics_list, away_fieldmetrics_list, fieldcand_list)
                        logging.debug("fieldcandlist=%s",fieldcand_list)
                        if len(fieldcand_list) > 1:
                            # see if fieldcand_list needs to be reduced:
                            # for each field, get the True/False list of game scheduled status
                            isgame_list = [(x,
                                            [y['isgame'] for y in self.fieldSeasonStatus[self.fstatus_indexerGet(x)]
                                             ['slotstatus_list'][round_id-1]])
                                           for x in fieldcand_list if self.fieldSeasonStatus[self.fstatus_indexerGet(x)]
                                           ['slotstatus_list'][round_id-1]]
                            if not isgame_list:
                                logging.warning("ftscheduler: fields %s not available on gameday %d", fieldcand_list, round_id)
                                submin += 1
                                continue
                            # recreate the isgame list
                            isgame_list[:] = [fieldsched for fieldsched in isgame_list if not all(fieldsched[1])]
                            if len(isgame_list) < len(fieldcand_list):
                                logging.info("ftscheduler:schedulegen: dropping candidate field size reduced from %d to %d",
                                             len(fieldcand_list), len(isgame_list))
                            if not isgame_list:
                                logging.warning("ftscheduler: fields %s are full, looking for alternates",
                                                [x[0] for x in isgame_list])
                                submin += 1
                                continue
                            else:
                                # recreate the field candidate list based on remaining fields in isgame_list
                                fieldcand_list[:] = [x[0] for x in isgame_list]


                        if len(fieldcand_list) > 1:
                            # take care of the case where a field is completely unscheduled - if it is,
                            # assign a game and credit both early and late game counters
                            fieldempty_list = [x[0] for x in isgame_list if all_value(x[1], False)]
                            if fieldempty_list:
                                field_id = fieldempty_list[0]
                                slot_index = 0
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                break

                            if el_state & EL_enum.EARLY_TEAM_NOTMET and el_state & EL_enum.EARLY_DIVTOTAL_NOTMET:
                                # if we have not met the early slot criteria, try to fill slot 0
                                # first create list of fields from candidate field list that has slot 0 open if any
                                firstslotopenfield_list = [x[0] for x in isgame_list if not x[1][0]]
                                if firstslotopenfield_list:
                                    # if slot 0 is open, take it
                                    field_id = firstslotopenfield_list[0] # take first field element
                                    slot_index = 0
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    logging.debug("ftscheduler:genschedule:multiple fieldcand el early, first slot open field=%d round=%d",
                                                  field_id, round_id)
                                    break # break out of while True loop
                                else:
                                    # if slot 0 is not open, first see if it makes sense to shift other scheduled slots
                                    # to open up slot 0
                                    # get list of fields that have games scheduled in slot 0
                                    firstslotscheduled_list = [x[0] for x in isgame_list if x[1][firstslot_CONST]]
                                    # get list of fields where slot 0 is already scheduled - this should be all of them
                                    if set(firstslotscheduled_list) != set(fieldcand_list):
                                        raise FieldConsistencyError(firstslotscheduled_list, fieldcand_list)
                                    # find out div and teams that are already scheduled for slot 0
                                    match_list = [{'field_id':x,
                                                   'match':self.fieldSeasonStatus[self.fstatus_indexerGet(x)]['slotstatus_list'][round_id-1][firstslot_CONST]['teams'],
                                                   'newslot':firstslot_CONST} for x in firstslotscheduled_list]
                                    fieldslot_tuple = self.compareCounterToTarget(match_list, 'early')
                                    if fieldslot_tuple:
                                        # if the current home and away early counts are both greater than
                                        # the target amount, they can afford to be bumped out the earliest
                                        # slots; current match will take its place at slot 0
                                        field_id = fieldslot_tuple.field_id
                                        slot_index = fieldslot_tuple.slot_index
                                        # shift the current scheduled games to the right one spot
                                        self.shiftFSstatus_list(field_id, round_id, slot_index)
                                        # update counters
                                        # increment for current home and away teams which will take first slot
                                        self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                        break

                            # get the list of the first open field for each field in fieldcand list
                            # do this assignent outside of the below if LATE.. statements because we will need it for
                            # for both the LATE counter situation and also the remaining generic non-late (or early)
                            # cases.
                            openslotfield_list = [(x[0], x[1].index(False)) for x in isgame_list
                                                  if not all(x[1])]
                            if el_state & EL_enum.LATE_TEAM_NOTMET and el_state & EL_enum.LATE_DIVTOTAL_NOTMET:
                                # if last slot should be scheduled, then find the last open slot in the currently scheduled set
                                # and insert this current match at that open slot - note that we are not necessarily
                                # scheduling at the very last slot of the day
                                # Note to prevent index value exceptions, don't add a list element if all of the 1-element list
                                # is true or the last element in the 1-element list is True (game already scheduled in the very
                                # last slot)
                                # note on handling exceptions within list comprehension - basically can't do
                                # http://stackoverflow.com/questions/1528237/how-can-i-handle-exceptions-in-a-list-comprehension-in-python
                                # find any fields that only have one element
                                # use http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
                                # modified for tuples
                                osf_indexerGet = lambda x: dict((p[1],i) for i,p in enumerate(openslotfield_list)).get(x)
                                # see if there are any fields with only one game scheduled so far
                                # even if there are multiple fields with only game, only one is returned as the dictionary creation
                                # process above with the lambda function will only allow one value to be re-mapped to a key
                                onegame_ind = osf_indexerGet(1)
                                if onegame_ind:
                                    field_id = openslotfield_list[onegame_ind][0]
                                    slot_index = 1
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    self.findTeamsDecrementEL_counters(field_id, round_id, 0, 'late')
                                    # we also need to decrement the late counters for slot 0
                                    break
                                # ok there are no fields with only one game scheduled - next what we are going to do now is to look
                                # at the fields and see if there are any last game matches that can afford to not be the last game
                                # anymore.  This is done by looking at the late counters and see if there any over the target count.
                                # Both home and away counters need to be over the target.
                                # dict 'field_id' is field_id, 'match' is the match info for the already-scheduled slot
                                # (we have to decrement open slot x[1] by 1 to get the scheduled game)
                                # new slot is the current open slot
                                match_list = [{'field_id':x[0],
                                               'match':self.fieldSeasonStatus[self.fstatus_indexerGet(x[0])]['slotstatus_list'][round_id-1][x[1]-1]['teams'],
                                               'newslot':x[1]} for x in openslotfield_list]
                                fieldslot_tuple = self.compareCounterToTarget(match_list, 'late')
                                if fieldslot_tuple:
                                    # if the current home and away late counts are both greater than
                                    # the target amount, they can afford to have the scheduled spot take up the last slot
                                    # fyi no shifting is necessary for 'late' (unlike for 'early' where shifting is needed when slot 0
                                    # is taken up)
                                    field_id = fieldslot_tuple.field_id
                                    slot_index = fieldslot_tuple.slot_index
                                    # increment for current home and away teams which will take last slot
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    break

                            # if fieldslot_tuple is empty, that means that we need the current last scheduled slot as is - so we need to
                            # schedule the current match into some slot besides the very first or last slot
                            # We will schedule it into second-to-last slot
                            # to find the field, we will use the field that has the least number of games scheduled
                            # ref http://stackoverflow.com/questions/3282823/python-get-key-with-the-least-value-from-a-dictionary
                            # but modified to work wit list of tuples - use itemgetter to get min based on 1-index element
                            # note we don't have to do any shifting
                            # we also don't need to update any counters
                            # this also applies to generic case where EL_enum is Normal (both early late counters have met target)
                            # CHANGE to above:
                            # For a normal (non-early, non-late) state, instead of always avoiding the first and last slots, we are
                            # going to look at the counters of the first and last slots.  If either of them have exceeded the target,
                            # we are going to replace the current match with that of the first or last slot.  If both first and last
                            # slot counters have exceeded the target, then the current match will replace the match as the slot with
                            # the largest difference compared to the target.
                            firstlastmatch_list = [{'field_id':x[0],
                                                    'firstmatch':self.fieldSeasonStatus[self.fstatus_indexerGet(x[0])]['slotstatus_list'][round_id-1][firstslot_CONST]['teams'],
                                                    'firstmatch_newslot':firstslot_CONST,
                                                    'lastmatch':self.fieldSeasonStatus[self.fstatus_indexerGet(x[0])]['slotstatus_list'][round_id-1][x[1]-1]['teams'],
                                                    'lastmatch_newslot':x[1]}
                                                   for x in openslotfield_list]

                            fieldslotELtype_tuple = self.findBestSlot(firstlastmatch_list)
                            if fieldslotELtype_tuple:
                                field_id = fieldslotELtype_tuple.field_id
                                slot_index = fieldslotELtype_tuple.slot_index
                                el_str = fieldslotELtype_tuple.el_str
                                if slot_index == 0 and el_str == 'early':
                                    # shift the current scheduled games to the right one spot
                                    self.shiftFSstatus_list(field_id, round_id, slot_index)
                                elif (slot_index == 0 and el_str != 'early') or (slot_index != 0 and el_str == 'early'):
                                    raise CodeLogicError("ftscheduler:findBestSlot slot_index el_str logic error")
                                # increment for current home and away teams which will take last slot
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_str)
                                break
                            else:
                                # for all other cases, schedule into second-to-last slot
                                minelem =  min(openslotfield_list, key=itemgetter(1))
                                field_id = minelem[0]
                                slot_index = minelem[1]-1  # -1 because we are scheduling into the second-to-last slot
                                self.shiftFSstatus_list(field_id, round_id, slot_index)
                                if slot_index == 0:
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    self.findTeamsDecrementEL_counters(field_id, round_id, 1, 'early')
                                break
                        else:
                            # handle case where there is only one candidate field
                            # logic of code follows that of the multiple fieldcand list case handled in the first part
                            # of the if....  See comments above.  Singe candidate field is a simplification of the
                            # multiple fieldcand case
                            field_id = fieldcand_list[0]
                            fsindex = self.fstatus_indexerGet(field_id)
                            # find status list for this round
                            fieldslotstatus_list = self.fieldSeasonStatus[fsindex]['slotstatus_list'][round_id-1]
                            # find first open time slot in round
                            if fieldslotstatus_list:
                                isgame_list = [y['isgame'] for y in fieldslotstatus_list]
                                if all(isgame_list):
                                    logging.warning("ftscheduler:schedulegenerator:field=%d round=%d full, attempting alternate",
                                                    field_id, round_id)
                                    submin += 1
                                    continue
                            else:
                                logging.warning("ftscheduler: field %d not available on gameday %d", field_id, round_id)
                                submin += 1
                                continue

                            if all_value(isgame_list, False):
                                # if there are no games scheduled for the field, assign to first slot
                                # and update both early/late counters
                                slot_index = firstslot_CONST
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                break
                            if el_state & EL_enum.EARLY_TEAM_NOTMET and el_state & EL_enum.EARLY_DIVTOTAL_NOTMET:
                                if not isgame_list[0]:
                                    # if no game scheduled in first slot, schedule it
                                    slot_index = firstslot_CONST
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    break # break out of while True loop
                                else:
                                    # as in the case for multiple fieldcand's - see if it makes sense to push out
                                    # the current slot-0-scheduled match
                                    match_list = [{'field_id':field_id,
                                                   'match':self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1][firstslot_CONST]['teams'],
                                                   'newslot':firstslot_CONST}]
                                    fieldslot_tuple = self.compareCounterToTarget(match_list, 'early')
                                    if fieldslot_tuple:
                                        # ok we can shift
                                        slot_index = fieldslot_tuple.slot_index # should be same as slot 0
                                        self.shiftFSstatus_list(field_id, round_id, slot_index)
                                        self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                        break

                            firstopenslot = isgame_list.index(False)
                            if el_state & EL_enum.LATE_TEAM_NOTMET and el_state & EL_enum.LATE_DIVTOTAL_NOTMET:
                                # see if there is only one game scheduled so far (assumed that game is scheduled
                                # in slot 0, which should always be the case)
                                if firstopenslot == 1:
                                    slot_index = 1
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    self.findTeamsDecrementEL_counters(field_id, round_id, 0, 'late')
                                    break
                                # as in the multiple fieldcand case, see if the last game can affort to not be the
                                # last game anymore - do this by looking at the late counters and seeing if it is over
                                # the target value (both home and away)
                                match_list = [{'field_id':field_id,
                                               'match':self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1][firstopenslot-1]['teams'],
                                               'newslot':firstopenslot}]
                                fieldslot_tuple = self.compareCounterToTarget(match_list, 'late')
                                if fieldslot_tuple:
                                    slot_index = fieldslot_tuple.slot_index
                                    # increment for current home and away teams which will take last slot
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    break
                            # for EL_enum 'normal' cases, see if it makes sense to take over first or last slot anyways
                            gamedayFieldStatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1]
                            firstlastmatch_list = [{'field_id':field_id,
                                                    'firstmatch':gamedayFieldStatus[firstslot_CONST]['teams'],
                                                    'firstmatch_newslot':firstslot_CONST,
                                                    'lastmatch':gamedayFieldStatus[firstopenslot-1]['teams'],
                                                    'lastmatch_newslot':firstopenslot}]
                            fieldslotELtype_tuple = self.findBestSlot(firstlastmatch_list)
                            if fieldslotELtype_tuple:
                                field_id = fieldslotELtype_tuple.field_id
                                slot_index = fieldslotELtype_tuple.slot_index
                                el_str = fieldslotELtype_tuple.el_str
                                if slot_index == 0 and el_str == 'early':
                                    # shift the current scheduled games to the right one spot
                                    self.shiftFSstatus_list(field_id, round_id, slot_index)
                                elif (slot_index == 0 and el_str != 'early') or (slot_index != 0 and el_str == 'early'):
                                    raise CodeLogicError("ftscheduler:findBestSlot slot_index el_str logic error")
                                # increment for current home and away teams which will take last slot
                                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_str)
                                break
                            else:
                                # for all other cases, schedule not at first available slot, but take the last
                                # scheduled slot - and shift the currently scheduled last slot over to the right one
                                slot_index = firstopenslot-1
                                self.shiftFSstatus_list(field_id, round_id, slot_index)
                                if slot_index == 0:
                                    # if we are inserting into slot0, then update appropriate EL counters
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    self.findTeamsDecrementEL_counters(field_id, round_id, 1, 'early')
                                break

                    # these get exected after while True breaks
                    logging.debug("ftscheduler: after timeslot=%d assign div=%d round_id=%d home_id=%d away_id=%d",
                                  slot_index, div_id, round_id, home_id, away_id)
                    logging.debug("ftscheduler: assign to field=%d slotind=%d home_currentel=%s away_currentel=%s",
                                  field_id, slot_index, home_currentel_dict, away_currentel_dict)
                    selected_ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1][slot_index]
                    selected_ftstatus['isgame'] = True
                    selected_ftstatus['teams'] = {'div_id': div_id, home_CONST:home_id, away_CONST:away_id}
                    gametime = selected_ftstatus['start_time']
                    home_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list))
                    away_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list))
                    home_fieldmetrics_list[home_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    away_fieldmetrics_list[away_fieldmetrics_indexer.get(field_id)]['count'] += 1

                    gameday_fieldcount[gd_fieldcount_indexerGet(field_id)]['count'] += 1
                    div = getAgeGenderDivision(div_id)
                    logging.debug("div=%s%s round_id=%d, field=%d gametime=%s slotindex=%d",
                                  div.age, div.gender, round_id, field_id, gametime, slot_index)
                logging.debug("ftscheduler: divlist=%s end of round=%d gameday_fieldcount=%s",
                              connected_div_list, round_id, gameday_fieldcount)
            self.ReFieldBalanceIteration(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet)
            # now work on time balanceing
            self.ReTimeBalance(fset, connected_div_list)
            self.ManualSwapTeams(fset, connected_div_list)
            self.ProcessConstraints(fset, connected_div_list)

            for field_id in fset:
                gameday_id = 1
                for gameday_list in self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list']:
                    if gameday_list:
                        for match in gameday_list:
                            if match['isgame']:
                                gametime = match['start_time']
                                teams = match['teams']
                                div_id = teams['div_id']
                                home_id = teams[home_CONST]
                                away_id = teams[away_CONST]
                                div = getAgeGenderDivision(div_id)
                                self.dbinterface.insertGameData(div.age, div.gender, gameday_id,
                                                                gametime.strftime(time_format_CONST),
                                                                field_id, home_id, away_id)
                    gameday_id += 1
        self.dbinterface.setSchedStatus_col()
        # executes after entire schedule for all divisions is generated
        #self.compactTimeSchedule()

    def ManualSwapTeams(self, fset, div_set):
        ''' Manual Swap Teams as specified in _swap_team_info in leaguedivprep '''
        for div_id in div_set:
            div_swapinfo_list = getSwapTeamInfo(div_id)
            if div_swapinfo_list:
                for div_swapinfo in div_swapinfo_list:
                    swapdiv_id = div_swapinfo['div_id']
                    team1_id = div_swapinfo['team1_id']
                    team2_id = div_swapinfo['team2_id']
                    for f in fset:
                        fslot_status = self.fieldSeasonStatus[self.fstatus_indexerGet(f)]['slotstatus_list']
                        for gamedayslot_status in fslot_status:
                            for slot_status in gamedayslot_status:
                                if slot_status['isgame']:
                                    teams = slot_status['teams']
                                    if teams['div_id'] == swapdiv_id:
                                        if teams[home_CONST] == team1_id:
                                            teams[home_CONST] = team2_id
                                        elif teams[home_CONST] == team2_id:
                                            teams[home_CONST] = team1_id
                                        if teams[away_CONST] == team1_id:
                                            teams[away_CONST] = team2_id
                                        elif teams[away_CONST] == team2_id:
                                            teams[away_CONST] = team1_id
                    # swap counter values also.  In addition to EL counters, we also need to swap field metric
                    # counters also.  However, field metric counters are no longer used at this point in code flow.
                    # TODO: review to find other - including field metric - counters to swap
                    cel_counter_list = self.current_earlylate_list[self.cel_indexerGet(swapdiv_id)]['counter_list']
                    tel_target_list = self.target_earlylate_list[self.tel_indexerGet(swapdiv_id)]['target_list']
                    # counter swaps
                    cel_counter_list[team1_id-1], cel_counter_list[team2_id-1] = \
                                                  cel_counter_list[team2_id-1], cel_counter_list[team1_id-1]
                    tel_target_list[team1_id-1], tel_target_list[team2_id-1] = \
                                                  tel_target_list[team2_id-1], tel_target_list[team1_id-1]



    def ReFieldBalanceIteration(self, connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet):
        old_balcount_list = self.CountFieldBalance(connected_div_list, fieldmetrics_list,
                                                   fieldmetrics_indexerGet)
        old_bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(old_balcount_list)).get(x)
        iteration_count = 1
        logging.debug("ftscheduler:refieldbalance: iteration=%d 1st balance count=%s", iteration_count,
                      old_balcount_list)
        while True:
            rebalance_count = self.ReFieldBalance(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet)
            balcount_list = self.CountFieldBalance(connected_div_list,fieldmetrics_list, fieldmetrics_indexerGet)
            bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(balcount_list)).get(x)
            balance_diff = [{'div_id':div_id,
                             'diff':old_balcount_list[old_bal_indexerGet(div_id)]['fcountdiff_num'] -
                             balcount_list[bal_indexerGet(div_id)]['fcountdiff_num']}
                            for div_id in connected_div_list]
            logging.debug("ftscheduler:refieldbalance: continuing iteration=%d balance count=%s diff=%s",
                          iteration_count, balcount_list, balance_diff)
            #print 'field iteration=', iteration_count, 'balance count=', balcount_list, 'diff=', balance_diff
            if all(x['diff'] < 1 for x in balance_diff) or iteration_count >= field_iteration_max_CONST:
                logging.debug("ftscheduler:refieldbalance: FINISHED FIELD iteration connected_div %s", connected_div_list)
                print 'finished field iteration div=', connected_div_list
                if iteration_count >= field_iteration_max_CONST:
                    logging.debug("ftscheduler:refieldbalance: iteration count exceeded max=%d", field_iteration_max_CONST)
                    print 'FINISHED but Iteration count > Max'
                break
            else:
                old_balcount_list = balcount_list
                old_bal_indexerGet = bal_indexerGet
                iteration_count += 1


    def shiftGameDaySlots(self, fieldstatus_round, isgame_list, field_id, gameday_id,
                          src_begin, dst_begin, shift_len):
        ''' shift gameday timeslots '''
        logging.debug("ftscheduler:compaction:shiftGameDayslots isgamelist=%s, field=%d gameday=%d src_begin=%d dst_begin=%d len=%d",
                      isgame_list, field_id, gameday_id, src_begin, dst_begin, shift_len)
        src_end = src_begin + shift_len
        dst_end = dst_begin + shift_len
        for i,j in zip(range(src_begin, src_end), range(dst_begin, dst_end)):
            srcslot = fieldstatus_round[i]
            dstslot = fieldstatus_round[j]
            if srcslot['isgame']:
                # if a game exists, shift to new time slot, and update db doc entry
                dstslot['isgame'] = srcslot['isgame']
                # if dstslot has a game (True field), then write to db
                self.dbinterface.updateGameTime(field_id, gameday_id,
                                                srcslot['start_time'].strftime(time_format_CONST),
                                                dstslot['start_time'].strftime(time_format_CONST))
            else:
                try:
                    nextTrue_ind = isgame_list[i:].index(True)
                except ValueError:
                    logging.error("ftscheduler:compact:shiftGameDayslots last game ends at %d", i-1)
                    for k in range(j, dst_end):
                        fieldstatus_round[k]['isgame'] = False
                else:
                    newsrc_begin = i + nextTrue_ind
                    # note +1 increment is important below when computing length from difference of indices
                    newshift_length = dst_end + 1 - newsrc_begin
                    newdst_begin = j
                    self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, gameday_id,
                                           src_begin=newsrc_begin, dst_begin=newdst_begin, shift_len=newshift_length)
                    for k in range(newdst_begin+newshift_length, dst_end):
                        fieldstatus_round[k]['isgame'] = False
                finally:
                    break

    def findFieldGamedayLastTrueSlot(self, field_id, gameday_id):
        gameday_fslot = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][gameday_id-1]
        isgame_list = [x['isgame']  for x in gameday_fslot]
        lastslot = len(isgame_list)-1-isgame_list[::-1].index(True)
        return lastslot

    def RecomputeCEL_list(self, fset, div_set):
        ''' recompute current_earlylist_counter structure by going through fieldseasonstatus matrix '''
        for div_id in div_set:
            # first clear counters
            divinfo = self.leaguediv[self.leaguediv_indexerGet(div_id)]
            numteams = divinfo['totalteams']
            for elcounter in self.current_earlylate_list[self.cel_indexerGet(div_id)]['counter_list']:
                elcounter['early'] = 0
                elcounter['late'] = 0
        for f in fset:
            fslot_status = self.fieldSeasonStatus[self.fstatus_indexerGet(f)]['slotstatus_list']
            for gameday_fslot in fslot_status:
                isgame_list = [x['isgame']  for x in gameday_fslot]
                lastslot = len(isgame_list)-1-isgame_list[::-1].index(True)
                for slot_index, el_type in zip([0, lastslot],['early','late']):
                    teams = gameday_fslot[slot_index]['teams']
                    div_id = teams['div_id']
                    home_id = teams[home_CONST]
                    away_id = teams[away_CONST]
                    cel_index = self.cel_indexerGet(div_id)
                    current_el_list = self.current_earlylate_list[cel_index]['counter_list']
                    home_currentel_dict = current_el_list[home_id-1]
                    away_currentel_dict = current_el_list[away_id-1]
                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)

    def mapStartTimeToSlot(self, startafter_time, firstgame_time, gameinterval):
        slot_counter = 0
        gametime = firstgame_time
        while gametime < startafter_time:
            gametime += gameinterval
            slot_counter += 1
        return slot_counter

    def mapEndTimeToSlot(self, endbefore_time, firstgame_time, gameinterval):
        slot_counter = -1
        endtime = firstgame_time + gameinterval
        while endtime <= endbefore_time:
            endtime += gameinterval
            slot_counter += 1
        return slot_counter

    def ProcessConstraints(self, fset, div_set):
        ''' process specified team constraints - see leaguedivprep data structure'''
        for div_id in div_set:
            divinfo = self.leaguediv[self.leaguediv_indexerGet(div_id)]
            ginterval = divinfo['gameinterval']
            gameinterval = timedelta(0,0,0,0,ginterval) # to be able to add time - see leaguedivprep fieldseasonstatus

            # get constraints for each div
            divconstraint_list = getTeamTimeConstraintInfo(div_id)
            if divconstraint_list:
                for constraint in divconstraint_list:
                    cdiv_id = constraint['div_id']
                    cteam_id = constraint['team_id']
                    cdesired_list = constraint['desired']
                    for cdesired in cdesired_list:
                        breakflag = False
                        # each time might have multiple constraints
                        # read each constraint and see if any are already met by default
                        cd_gameday_id = cdesired['gameday_id']
                        cd_id = cdesired['id']
                        cd_priority = cdesired['priority']
                        startafter_str = cdesired.get('start_after')
                        startafter_time = parser.parse(startafter_str) if startafter_str else None
                        endbefore_str = cdesired.get('end_before')
                        endbefore_time = parser.parse(endbefore_str) if endbefore_str else None
                        # we can support two separate continuous segments of desired slots (but not more than two)
                        # define the type of segment basd on presend of start and endtimes and their values
                        # comment visually shows time slots (not position accurate) that will satisfy time constraints
                        segment_type = -1
                        if startafter_time and not endbefore_time:
                            # [------TTTT]
                            segment_type = 0
                        elif not startafter_time and endbefore_time:
                            # [TTTT------]
                            segment_type = 1
                        elif startafter_time and endbefore_time:
                            if endbefore_time > startafter_time:
                                # [---TTTTTT---]
                                segment_type = 2
                            elif endbefore_time < startafter_time:
                                #[TTTT----TTTTT]
                                segment_type = 3
                            elif endbefore_time == startafter_time:
                                # [TTTTTTTTTTTT] (no constraint)
                                logging.debug("ftscheduler:processconstraints: constraint %d is not needed since start_after=end_before",
                                              cd_id)
                                break
                        else:
                            logging.debug("ftscheduler:processconstraints: constraint %d nothing specified",
                                          cd_id)
                            break
                        swapmatch_list = []
                        for f in fset:
                            # search through each field for the divset to 1)find if team is already scheduled in a desired slot; or
                            # 2) if not, find the list of matches that the team can swap with during that day
                            fstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(f)]
                            f_gameslotsperday = fstatus['gameslotsperday']
                            fstatus_gameday = \
                              self.fieldSeasonStatus[self.fstatus_indexerGet(f)]['slotstatus_list'][cd_gameday_id-1]

                            # find out slot number that is designated by the 'start_after' constraint
                            firstgame_slot = fstatus_gameday[0]
                            if not firstgame_slot or not firstgame_slot['isgame']:
                                raise CodeLogicError("ftscheduler:ProccessContraints: firstgame for div %d, gameday %d" % (cdiv_id, cd_gameday_id))
                            firstgame_time = firstgame_slot['start_time']  # first game time
                            startafter_index = self.mapStartTimeToSlot(startafter_time, firstgame_time, gameinterval) if startafter_time else None
                            if startafter_index and startafter_index > f_gameslotsperday - 1:
                                raise SchedulerConfigurationError("Constraint Configuration Error: Start after time is too late")

                            # -1 return means that the end time is before the end of the first game
                            endbefore_index = self.mapEndTimeToSlot(endbefore_time, firstgame_time, gameinterval) if endbefore_time else -2

                            fullindex_list = range(f_gameslotsperday)
                            # define range of time slots that satisfy constraints
                            if segment_type == 0:
                                segment_range = range(startafter_index, f_gameslotsperday)
                            elif segment_type == 1:
                                segment_range = range(0, endbefore_index+1)
                            elif segment_type == 2:
                                segment_range = range(startafter_index, endbefore_index+1)
                            elif segment_type == 3:
                                segment_range = range(0,endbefore_index+1) + range(startafter_index, f_gameslotsperday)
                            else:
                                # ref http://www.diveintopython.net/native_data_types/formatting_strings.html for formatting string
                                raise CodeLogicError("ftscheduler:process constraints - error with segment type, constraint %d" %(cd_id,))
                            # based on segment range, create list with T/F values - True represents slot that satisfies
                            # time constraint
                            canswapTF_list = [True if x in segment_range else False for x in fullindex_list]
                            #print 'cd id canswap', cd_id, canswapTF_list
                            for slot_ind, slot_TF in enumerate(canswapTF_list):
                                if slot_TF:
                                    fstatus_slot = fstatus_gameday[slot_ind]
                                    # search through gameday slots where game is already scheduled
                                    if fstatus_slot['isgame']:
                                        teams = fstatus_slot['teams']
                                        div_id = teams['div_id']
                                        home = teams[home_CONST]
                                        away = teams[away_CONST]
                                        if div_id == cdiv_id and (home == cteam_id or away == cteam_id):
                                            logging.info("ftscheduler:constraints: ***constraint satisfied with constraint=%d div=%d team=%d gameday=%d",
                                                         cd_id, div_id, cteam_id, cd_gameday_id)
                                            breakflag = True
                                            break  # from inner for canswapTF_list loop
                                        else:
                                            swapmatch_list.append({'teams':teams, 'slot_index':slot_ind, 'field_id':f})
                            else:
                                logging.debug("ftscheduler:processconstraints:candidate matches in field=%d constraint=%d for swap %s",
                                              f, cd_id, swapmatch_list)
                                continue
                            break  # from outer for fset loop
                        if breakflag:
                            logging.debug("ftscheduler:processconstraints id %d %s already satisfied as is", cd_id, cdesired)
                            print '*********constraint', cd_id, cdesired, 'is already satisfied'
                        else:
                            logging.debug("ftscheduler:processconstraints: id=%d constraint=%s candidate swap=%s",
                                          cd_id, cdesired, swapmatch_list)
                            print '####constraint', cd_id, cdesired
                            self.findMatchSwapForConstraint(fset, cdiv_id, cteam_id, cd_gameday_id, cd_priority, swapmatch_list)

    def findMatchSwapForConstraint(self, fset, div_id, team_id, gameday_id, priority, swap_list):
        ''' from the list of candidate matches to swap with, find match to swap with that does not violate constraints.
        Priority description:
        Priority 1: Use cost calculations - however, if refslot is an EL slot, if the EL cost of the opposite slot is
        above a threshold, then skip to next iteration; if EL cost is below the threshold,
        then increase mult weight when swap slot is an EL slot
        Priority 2: Use cost calculations - however, if refslot is an EL slot, then swap slot must also be an EL slot;
        but if the EL cost of the opposite slot exceeds a priority-dependent threshold, skip iteration.
        if ref slot is not an EL slot, then increase mult weight when swap slot is an EL slot
        Priority 3: Use cost calucations - however, if refslot is an EL slot, then disallow that particular constraint
        Don't let a match swap in a ref EL slot, even if swap slot is an EL slot; however, if swap slot is an EL slot,
        do normal calculations - with slightly higher mult weight'''
        # Teams that swap may get additional early/late games
        # first find slot that matches current reference team
        swap_addweight = 0
        swap_multweight = 1
        requireEarly_flag = False
        requireLate_flag = False
        fstatus_tuple = self.findFieldSeasonStatusSlot(fset, div_id, team_id, gameday_id)
        refteams = fstatus_tuple.teams
        reffield_id = fstatus_tuple.field_id
        refslot_index = fstatus_tuple.slot_index
        refoppteam_id = fstatus_tuple.oppteam_id
        lastTrueSlot = self.findFieldGamedayLastTrueSlot(reffield_id, gameday_id)
        # note we will most likely continue to ignore refoppteam_cost value below as it has no
        # bearing on max operation (same value for all swap candidates)
        if refslot_index == 0:
            refoppteam_cost = self.getSingleTeamELstats(div_id, refoppteam_id, 'early')
        elif refslot_index == lastTrueSlot:
            refoppteam_cost = self.getSingleTeamELstats(div_id, refoppteam_id, 'late')
        else:
            refoppteam_cost = 0

        # ********* cost parameters
        if (refslot_index == 0 or refslot_index == lastTrueSlot):
            if priority == 3:
                print '*** priority 3, refslot is EL, NONE dont be mean'
                logging.debug("ftscheduler:findMatchSwapConstraint: teams %s is an EL slot, no swap",
                              refteams)
                return None
            elif priority == 2 or priority == 1:
                # if ref slot is an EL slot, swap slot needs to also be an EL slot
                if refslot_index == 0:
                    requireLate_flag = True
                else:
                    requireEarly_flag = True

        #slist_field_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(swap_list)).get(x)
        samefield_index_list = [i for i,j in enumerate(swap_list) if j['field_id']==reffield_id]
        #print 'div team gameday slot field index', div_id, team_id, gameday_id, refslot_index, reffield_id, samefield_index_list
        if samefield_index_list:
            cost_list = []
            for swap_index in samefield_index_list:
                swap_elem = swap_list[swap_index]
                swap_slot_index = swap_elem['slot_index']
                EL_slot_state = (swap_slot_index == 0 or swap_slot_index == lastTrueSlot)
                swap_cost_threshold = 1 if priority == 1 else 0  # priority dependent threshold
                # ************ more cost logic
                if (priority == 2 and (requireEarly_flag or requireLate_flag)) and not EL_slot_state:
                    continue
                elif requireEarly_flag and swap_slot_index == 0:
                    refoppteam_swap_cost = self.getSingleTeamELstats(div_id, refoppteam_id, 'early')
                    if refoppteam_swap_cost >= swap_cost_threshold:
                        continue
                elif requireLate_flag and swap_slot_index == lastTrueSlot:
                    refoppteam_swap_cost = self.getSingleTeamELstats(div_id, refoppteam_id, 'late')
                    if refoppteam_swap_cost >= swap_cost_threshold:
                        continue
                elif ((priority == 2 and EL_slot_state) or
                      (priority == 1 and (requireEarly_flag or requireLate_flag) and EL_slot_state)):
                    swap_multweight = 2
                elif priority ==3 and EL_slot_state:
                    swap_addweight = 1
                swap_teams = swap_elem['teams']
                # cost for swap teams current cost in current slot = attractive cost for swap teams to move out
                # from current slot
                # weight applied only if value is positive - since we are maximizing and want to attract if swap slot
                # is an EL slot (based on priority)
                swap_cost = self.getELcost_by_slot(swap_slot_index, swap_teams, lastTrueSlot)
                # ******** cost arithmetic using parameters
                if swap_cost > 0:
                    swap_cost = (swap_multweight*swap_cost) + swap_addweight
                # cost for swap teams to move into refslot (subtractive cost)
                swap_outgoing_cost = self.getELcost_by_slot(refslot_index, swap_teams, lastTrueSlot)
                # cost for ref teams to move into swapslot (subtractive)
                swap_incoming_cost = self.getELcost_by_slot(swap_slot_index, refteams, lastTrueSlot)
                if swap_incoming_cost < 0:
                    swap_incoming_cost = (swap_multweight*swap_incoming_cost) + swap_addweight
                total_cost = swap_cost - swap_outgoing_cost - swap_incoming_cost
                swap_list[swap_index]['swap_cost'] = swap_cost
                swap_list[swap_index]['swap_outgoing_cost'] = swap_outgoing_cost
                swap_list[swap_index]['swap_incoming_cost'] = swap_incoming_cost
                swap_list[swap_index]['total_cost'] = swap_cost - swap_outgoing_cost - swap_incoming_cost
                cost_list.append(swap_list[swap_index])
            if cost_list:
                max_swap = max(cost_list, key=itemgetter('total_cost'))
                logging.debug("ftscheduler:findMatchSwapConstraints: max swap elem", max_swap)
                #print 'max_swap', max_swap
                if max_swap['field_id'] != reffield_id:
                    raise CodeLogicError("ftschedule:findSwapMatchForConstraints reffield %d max_swap field do Not match" % (reffield_id,))
                fgameday_status = self.fieldSeasonStatus[self.fstatus_indexerGet(reffield_id)]['slotstatus_list'][gameday_id-1]
                if fgameday_status[refslot_index]['teams'] !=  refteams:
                    raise CodeLogicError("ftschedule:findSwapMatchConstraints refslotindex %d does not produce teams %s"
                                         % (refslot_index, refteams))
                max_swap_slot_index = max_swap['slot_index']
                max_swap_teams = max_swap['teams']
                if fgameday_status[max_swap_slot_index]['teams'] != max_swap_teams:
                    raise CodeLogicError("ftschedule:findSwapMatchConstraints swapslot %d does not produce teams %s"
                                         % (max_swap_slot_index, max_swap_teams))
                fgameday_status[refslot_index]['teams'], fgameday_status[max_swap_slot_index]['teams'] = \
                  fgameday_status[max_swap_slot_index]['teams'], fgameday_status[refslot_index]['teams']
                logging.debug("ftscheduler:swapmatchconstraints: swapping refslot %d with slot %d, refteams %s with teams %s",
                              refslot_index, max_swap_slot_index, refteams, max_swap_teams)
                print "****swapping refslot %d with slot %d, refteams %s with teams %s" % (refslot_index, max_swap_slot_index, refteams, max_swap_teams)

                self.updateSlotELCounters(refslot_index, max_swap_slot_index, refteams, max_swap_teams,
                                          lastTrueSlot, lastTrueSlot)
            else:
                logging.debug("ftscheduler:findMatchSwapConstraints cost list is empty, No Swap")
                print '*** No elements left in cost_list, NONE'
                return None
        else:
            print '****No options in the same field, returning NONE'
            return None


    def findFieldSeasonStatusSlot(self, fset, div_id, team_id, gameday_id):
        breakflag = False
        for f in fset:
            fgameday_status = self.fieldSeasonStatus[self.fstatus_indexerGet(f)]['slotstatus_list'][gameday_id-1]
            for slot_index, fstatus in enumerate(fgameday_status):
                if fstatus['isgame']:
                    fteams = fstatus['teams']
                    if fteams['div_id'] == div_id and (fteams[home_CONST]==team_id or fteams[away_CONST]==team_id):
                        oppteam_id = fteams[home_CONST] if fteams[away_CONST]==team_id else fteams[away_CONST]
                        breakflag = True
                        break
            else:
                continue
            break
        if breakflag:
            StatusSlot_tuple = namedtuple('StatusSlot_tuple', 'slot_index field_id oppteam_id teams')
            return StatusSlot_tuple(slot_index, f, oppteam_id, fteams)
        else:
            raise CodeLogicError("constraints: findswapmatch can't find slot for div=%d team=%d gameday=%d" % (div_id, team_id, gameday_id))

    def compactTimeSchedule(self):
        ''' compact time schedule by identifying scheduling gaps through False statueses in the 'isgame' field '''
        for fieldstatus in self.fieldSeasonStatus:
            field_id = fieldstatus['field_id']
            gameday_id = 1
            for fieldstatus_round in fieldstatus['slotstatus_list']:
                isgame_list = [x['isgame'] for x in fieldstatus_round]
                #print "compactSchedule: field_id, isgame_list", fieldstatus['field_id'], isgame_list
                # http://stackoverflow.com/questions/522372/finding-first-and-last-index-of-some-value-in-a-list-in-python
                # first find if there are any gamedays where the first game is not held on the first
                # available time slot for that field
                # catch index errors below
                try:
                    firstgame_ind = isgame_list.index(True)
                except ValueError:
                    logging.error("ftscheduler:compactTimeScheduler: No games scheduled on field %d gameday %d",
                                  field_id, gameday_id)
                    continue
                else:
                    fieldstatus_len = len(fieldstatus_round)
                    if firstgame_ind != 0:
                        dst_begin = 0
                        shift_length = fieldstatus_len - firstgame_ind
                        # no game at early time slot, shift all games so schedule for day begins at earliest slot
                        # (note defaulting first game to earliest time slot may change in the future)
                        # function compacts all remaining gaps (only one call to shiftGameDaySlots needed)
                        logging.info("ftscheduler:compaction field=%d gameday=%d shift to daybreak first slot",
                                     field_id, gameday_id)
                        self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, gameday_id,
                                               src_begin=firstgame_ind, dst_begin=dst_begin, shift_len=shift_length)
                        for i in range(dst_begin+shift_length, fieldstatus_len):
                            fieldstatus_round[i]['isgame'] = False
                    else:
                        # Game in first slot, iterate from this point to find and compact time schedule gaps.
                        try:
                            false_ind = isgame_list.index(False)
                        except ValueError:
                            logging.error("ftscheduler:compaction:field=%d gameday=%d is full", field_id, gameday_id)
                            # all slots filled w. games, no False state
                            continue
                        else:
                            if false_ind == 0:
                                # this should not happen based on if else
                                raise TimeCompactionError(field_id, gameday_id)
                            try:
                                true_ind = isgame_list[false_ind:].index(True)
                            except ValueError:
                                logging.error("ftscheduler:compaction:field=%d gameday=%d no more gaps; gameday schedule is continuous and good",
                                              field_id, gameday_id)
                                # all slots filled w. games, no False state
                                continue
                            else:
                                # amount of status indices we are shifting is the beginning of the current 'true' segment until the
                                # end of the list
                                dst_begin = false_ind
                                src_begin = false_ind + true_ind
                                shift_length = fieldstatus_len - src_begin
                                logging.debug("ftscheduler:compaction:blockshift for field=%d gameday=%d from ind=%d to %d",
                                              field_id, gameday_id, src_begin, dst_begin)
                                self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, gameday_id,
                                                       src_begin=src_begin, dst_begin=dst_begin, shift_len=shift_length)
                                for i in range(dst_begin+shift_length, fieldstatus_len):
                                    fieldstatus_round[i]['isgame'] = False
                finally:
                    gameday_id += 1
