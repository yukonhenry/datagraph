''' Copyright YukonTR 2013 '''
from datetime import  datetime, timedelta
from itertools import groupby, chain
from schedule_util import roundrobin, all_same, all_value, enum, shift_list, \
    bipartiteMatch, getConnectedDivisionGroup, getDivFieldEdgeWeight_list,\
    all_isless, find_ge, find_le
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getSwapTeamInfo
import logging
from operator import itemgetter
from copy import deepcopy
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, \
     CodeLogicError, SchedulerConfigurationError
from math import ceil, floor
from collections import namedtuple, deque, Counter
import networkx as nx
from random import shuffle

bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
home_CONST = 'HOME'
away_CONST = 'AWAY'
venue_count_CONST = 'VCNT'
home_index_CONST = 0
away_index_CONST = 1
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
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python
date_format_CONST = '%m/%d/%Y'
#http://www.tutorialspoint.com/python/python_classes_objects.htm

#https://docs.python.org/2/library/datetime.html
_absolute_earliest_time = parser.parse('05:00').time()
_absolute_earliest_date = parser.parse('01/01/2010').date()

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class FieldTimeScheduleGenerator:
    def __init__(self, dbinterface, divinfo_tuple, fieldinfo_tuple, prefinfo_triple=None, pdbinterface=None, tminfo_tuple=None):
        self.divinfo_list = divinfo_tuple.dict_list
        #self.divinfo_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.divinfo_list)).get(x)
        self.divinfo_indexerGet = divinfo_tuple.indexerGet
        self.divinfo_tuple = divinfo_tuple
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.fieldinfo_indexerGet = fieldinfo_tuple.indexerGet
        # pref list use is optional
        if prefinfo_triple:
            self.prefinfo_list = prefinfo_triple.dict_list
            self.prefinfo_indexerGet = prefinfo_triple.indexerGet
            self.prefinfo_indexerMatch = prefinfo_triple.indexerMatch
            # pdbinterface is used to write back constraint satisfaction results
            # back to db through preference dbinterface
            self.pdbinterface=pdbinterface
        else:
            self.prefinfo_list = None
            self.prefinfo_indexerGet = None
            self.prefinfo_indexerMatch = None
        # team list use is optional also - contains field affinity info
        if tminfo_tuple:
            self.tminfo_list = tminfo_tuple.dict_list
            # for indexerGet, parameter is two-tuple (div_id, tm_id)
            # returns None or index into tminfo_list
            self.tminfo_indexerGet = tminfo_tuple.indexerGet
            # for indexerMatch
            self.tminfo_indexerMatch = tminfo_tuple.indexerMatch
        else:
            self.tminfo_list = None
            self.tminfo_indexerMatch = None
        # get connected divisions through shared fields
        self.connected_div_components = getConnectedDivisionGroup(self.fieldinfo_list, key='primaryuse_list')
        fstatus_tuple = self.getFieldSeasonStatus_list()
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        #logging.debug("fieldseasonstatus init=%s",self.fieldstatus_list)
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.divinfo_list)+1):
            self.total_game_dict[i] = []
        self.dbinterface = dbinterface
        self.current_earlylate_list = []
        self.target_earlylate_list = []
        self.cel_indexerGet = None
        self.tel_indexerGet = None
        # timegap_list tracks the last scheduled gametime for each team, which is
        # used to calculate the earliest candidate gametime for the next game while
        # honoring the minimum gap time between consecutive games.
        self.timegap_list = []
        self.timegap_indexerMatch = None

    def findMinimumCountField(self, homemetrics_list, awaymetrics_list, rd_fieldcount, requiredslots_num, home_hf_list, away_hf_list, submin=0):
        # NOTE: Calling this function assumes we are trying to balance across fields
        # return field_id(s) (can be more than one) that corresponds to the minimum
        # count in the two metrics list.  the minimum should map to the same field in both
        # metric lists, but to take into account cases where field_id with min count is different
        # between two lists, use sum of counts as metric.
        # return field_id(s) - not indices
        #optional parameter submin is used when the submin-th minimum is required, i.e. is submin=1
        #return the 2nd-most minimum count fields
        # Also pass in the minmaxdate_list and field_list - we want to find fields that satisfy
        # the minimum-date criteria - fill up fields on earlier calendar date
        # before starting to fill a later calendar date, even if violating field
        # count balancing requirements.  For example, if Field 1 is available on
        # Saturdays only and Field 2 is available on Sundays only - if teams
        # are only playing once during that weekend, have them play on Field1
        # on Saturdays until they have to play on Sunday/Field 2 because Sat/
        # Field1 is full, even though this will not meet field balancing
        # requirements.
        requiredslots_perfield = int(ceil(float(requiredslots_num)/len(rd_fieldcount)))
        maxedout_field = None
        almostmaxed_field = None

        # get count/field dict with maximum count
        maxgd = max(rd_fieldcount, key=itemgetter('count'))
        #for gd in rd_fieldcount:
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
        # get full home field lists(e.g. home field for 'away'-designated teams)
        # if there are no fields specified, then default to full list for that
        # team; else predicate can be either home_field_list or away_field_list
        home_hf_list = home_hf_list if home_hf_list else home_field_list
        away_hf_list = away_hf_list if away_hf_list else away_field_list

        if maxedout_field:
            maxedout_ind = home_field_list.index(maxedout_field)
            # when scaling, increment by 1 as fieldcount maybe 0
            # since homecount_list and awaycount_list are made from the respective
            # sorted (according to field) metrics list, maxedout_ind should
            # correspond to the maxed field for both homecount and awaycount lists
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
        minind = [i for i,j in enumerate(sumcount_list) if j == minsum]
        # doesn't matter below if we use home_field_list or away_field_list - should produce same results since both lists are created from metrics lists
        # that are sorted according to field_id
        mincount_fields = [home_field_list[i] for i in minind]
        uniquesumcount_list = list(set(sumcount_list))
        sumsortedfield_list = [{'sumcount':x,
            'field_list':[home_field_list[i] for i,j in enumerate(sumcount_list) if j==x]} for x in uniquesumcount_list]
        sumsortedfield_list.sort(key=itemgetter('sumcount'))
        #sumsortedfield_list[:] = [x.update({'priority':i}) for i,x in enumerate(sumsortedfield_list, start=1)]
        #return mincount_fields
        return sumsortedfield_list

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

    def findTeamsDecrementEL_counters(self, field_id, slot_index, el_str, fieldday_id):
        ''' find teams from fieldSeasonStatus list and decrement early/late counters'''
        fieldstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
        slotstatus_list = fieldstatus_list['slotstatus_list']
        rg_index = fieldday_id-1
        slotteams = slotstatus_list[rg_index]['sstatus_list'][slot_index]['teams']
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
        ''' find single potential match to swap with; also calculate costs so that
        optimization can be made '''
        # TODO: review logic here after implementation of fielday_id + round_id combination
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
                        fieldstatus_list= self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
                        slotstatus_list = fieldstatus_list['slotstatus_list']
                        for fieldday_id, slotstatus in enumerate(slotstatus_list, start=1):
                            if not slotstatus:
                                continue
                            sstatus_list = slotstatus['sstatus_list']
                            isgame_list = [x['isgame'] for x in sstatus_list]
                            if any(isgame_list):
                                # check for any() to make sure that at least one slot has been scheduled.
                                # for every field and fieldday_id, find game with team_id that falls on EL slot
                                lastslot = len(isgame_list)-1-isgame_list[::-1].index(True)
                                slot_index = 0 if el_type == 'early' else lastslot
                                # we are just going to search for matches in the early/late slot
                                match_teams = sstatus_list[slot_index]['teams']
                                if match_teams['div_id'] == div_id and \
                                    (match_teams[home_CONST] == team_id or match_teams[away_CONST] == team_id):
                                    # if a match is found, find opponent and it's cost
                                    oppteam_id = match_teams[home_CONST] if match_teams[away_CONST] == team_id else match_teams[away_CONST]
                                    oppteam_cost = self.getSingleTeamELstats(div_id, oppteam_id, el_type)
                                    logging.debug("ftscheduler:FindSwapMatchForTB: found slot0 field=%d div=%d fieldday=%d team=%d opp=%d",
                                        field_id,div_id, fieldday_id, team_id,
                                        oppteam_id)
                                    # only look for range that does not involve EL slots
                                    swapmatch_list = [{'swapteams':sstatus_list[x]['teams'],
                                        'cost':self.getELstats(sstatus_list[x]['teams'], el_type).measure,
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
                                            'min_cost':min_cost,
                                            'fieldday_id':fieldday_id,
                                            'field_id':field_id, 'team_id':team_id,
                                            'oppteam_id':oppteam_id,
                                            'oppteam_cost':oppteam_cost,
                                            'team_slot':slot_index,
                                            'self_teams':match_teams,
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
                        fieldday_id = max_min_swapmatch['fieldday_id']
                        ftstatus = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]['slotstatus_list'][fieldday_id-1]['sstatus_list']
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
                        #print 'lastslot', lastslot, div_id, field_id, fieldday_id, el_teams, swap_teams
                        self.updateSlotELCounters(el_slot_index, swap_slot_index,
                            el_teams, swap_teams, lastel_slot, None)
                        # swap slot does not occupy a list lastslot
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
                key_tuple = swap['field_id'], swap['fieldday_id']
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
            fieldday_id = swap_key[1]
            bgraph = swap_dict[swap_key]
            # get last slot information, if it exists (emedded in graph as one of the keys, the other being 0)
            lastslot = None
            for key in bgraph:
                if key > 0:
                    lastslot = key
                    break
            obj = bipartiteMatch(bgraph)
            # obj[0] contains the swap slots in a:b dictionary element - swap slot a w. b
            #print 'field gameday graph swapobj', field_id, fieldday_id, bgraph, obj[0]
            ftstatus = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]['slotstatus_list'][fieldday_id-1]
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
                status = self.FindSwapMatchForTimeBalance(div_id, fieldset,
                    diff_groups, el_type, random=random_count, offset=offset_count)

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
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            # http://stackoverflow.com/questions/10543303/number-of-values-in-a-list-greater-than-a-certain-number
            # count occurrences of diff between max and min counts are > 1, per
            # div_id
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

    def ReFieldBalance(self, connected_div_list, fieldmetrics_list, findexerGet, commondates_list):
        rebalance_count = 0
        for div_id in connected_div_list:
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            for team_id, team_metrics in enumerate(tfmetrics, start=1):
                # for each team in the division, get counts for fields with maximum/minimum use counts
                hi_use = max(team_metrics, key=itemgetter('count'))
                lo_use = min(team_metrics, key=itemgetter('count'))
                diff = hi_use['count']-lo_use['count']
                if diff > 1:
                    # if the difference between max and min is greater than a threshold
                    # (1 in this case), that meas the current team_id is favoring
                    # the use of hifield_id over lofield_id. See if it is possible to
                    # move a game between two fields if they are available on the
                    # same day
                    hifield_id = hi_use['field_id']
                    lofield_id = lo_use['field_id']
                    hi_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(hifield_id)]['slotstatus_list']
                    lo_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(lofield_id)]['slotstatus_list']
                    hi_team_metrics_list = []
                    lo_team_metrics_list = []
                    gameday_totalcost_list = []
                    #for fieldday_id, (hi_ftstatus, lo_ftstatus) in enumerate(zip(hi_ftstatus_list, lo_ftstatus_list),start=1):
                    for commondates_dict in commondates_list:
                        common_date = commondates_dict['date']
                        # work off of dates that are shared between the max and min
                        # fields - first get the corresponding fieldday_id
                        hi_fieldday_id = commondates_dict['map_dict'][hifield_id]
                        lo_fieldday_id = commondates_dict['map_dict'][lofield_id]
                        # we could also use an indexerGet function with fieldday_id
                        # as an argument, but we are being lazy here using the index
                        hi_ftstatus = hi_ftstatus_list[hi_fieldday_id-1]
                        lo_ftstatus = lo_ftstatus_list[lo_fieldday_id-1]
                        # for each gameday first find game stats for max count fields
                        # for max count fields, find for each gameday, each gameday slot where the target
                        # team plays on the max count field.  Each gameday slot might not involve the
                        # target team because they may be playing on a different field
                        logging.debug("continuing on maxfieldday=%d minfieldday=%d", hi_fieldday_id, lo_fieldday_id)
                        today_hifield_info_list = [{
                            'slot_index':i, 'start_time':j['start_time'],
                            'teams':j['teams']}
                            for i,j in enumerate(hi_ftstatus['sstatus_list'])
                            if j['isgame'] and j['teams']['div_id']==div_id and
                            (j['teams'][home_CONST]==team_id or j['teams'][away_CONST]==team_id)]
                        if len(today_hifield_info_list) > 1:
                            logging.info("ftscheduler:rebalance:today maxfieldinfo_list entry len is %d",
                                len(today_hifield_info_list))
                            #raise CodeLogicError('ftschedule:rebalance: There should only be one game per gameday')
                        if today_hifield_info_list:
                            logging.info("ftscheduler:refieldbalance: div=%d hifieldday=%d lofieldday=%d hifield_id=%d lofield_id=%d",
                                div_id, hi_fieldday_id, lo_fieldday_id,
                                hifield_id, lofield_id)
                            # assuming one game per team per day when taking 0-element
                            today_hifield_info = today_hifield_info_list[0]
                            logging.debug("ftscheduler:refieldbalance: hifield_id info=%s", today_hifield_info)
                            # if there is game being played on the max count field by the current team, then first find out
                            # find out how the potential time slot change associated with the field move might affect
                            #early/late time slot counters
                            isgame_list = [x['isgame'] for x in hi_ftstatus['sstatus_list']]
                            # find 0-index for last game (True) (last game may be in a different division)
                            lastTrue_slot = len(isgame_list)-1-isgame_list[::-1].index(True)
                            hi_slot = today_hifield_info['slot_index']
                            hi_teams = today_hifield_info['teams']
                            el_measure = self.getELcost_by_slot(hi_slot, hi_teams,
                                lastTrue_slot)
                            logging.debug('ftscheduler:refieldbalance: hi_slot=%d el_measure=%d lastslot=%d',
                                          hi_slot, el_measure, lastTrue_slot)

                            # Next find out who the opponent team is, then find out the field count (for the max count
                            # field) for that opponent team.  We need the count for the opponent because it will affect
                            # it's field count if the game is moved away from the max count field
                            oppteam_id = hi_teams[home_CONST] if hi_teams[away_CONST]==team_id else hi_teams[away_CONST]
                            hifield_opp_count = self.getFieldTeamCount(tfmetrics, hifield_id, oppteam_id)
                            lofield_opp_count = self.getFieldTeamCount(tfmetrics, lofield_id, oppteam_id)
                            # the measure for opponent team - desirability to swap out this game - is just the difference
                            # between max and min field counts
                            opp_measure = hifield_opp_count - lofield_opp_count
                            # *****
                            # Calculate Total cost for swapping out the hifield_id game (with the designated team_id) in the
                            # current gameday.
                            # total cost = early/late swap out measure (if slot is 0 or last) +
                            # opponent team max min field count diff (opp_measure) +
                            # we might want to scale the opp_measure over the el_measure as we are focused on field
                            # balacning - leave equal weight for now
                            hi_total_cost = el_measure + balanceweight_CONST*opp_measure
                            # summarize all the info and metrics for the swapped-out game from the max count field
                            # hi_team_metrics_list persists outside of this current gameday and is used to choose the
                            # best match involving the maxfteam out of all the gamedays to swap out
                            hi_team_metrics = {'team':team_id,
                                'oppteam_id':oppteam_id,
                                'hi_count':hifield_opp_count,
                                'lo_count':lofield_opp_count,
                                'opp_measure':opp_measure,
                                'fieldday_id':hi_fieldday_id,
                                'el_measure':el_measure,
                                'hi_total_cost':hi_total_cost}
                            hi_team_metrics_list.append(hi_team_metrics)
                            logging.debug('ftscheduler:refieldbalance: hifield_id team metrics=%s', hi_team_metrics)
                            # Now we are going to find all the teams (not just in this div but also all field-shared divs)
                            # using the minimum count field
                            # and then find the measures for each field - which is both the lofield_id counts for the home and
                            # away teams, along with the timeslot early/late count - el count only generated if the slot index
                            # falls under the 0 or last slot
                            # move some fields to general for loop as list comprehension gets too messy.
                            lo_sstatus_list = lo_ftstatus['sstatus_list']
                            today_lofield_info = [{'slot_index':i,
                                'teams':j['teams']}
                                for i,j in enumerate(lo_sstatus_list) if j['isgame']]
                            lo_isgame_list = [x['isgame'] for x in lo_sstatus_list]
                            # find 0-index for last game (True) (last game may be in a different division)
                            lo_lastTrue_slot = len(lo_isgame_list)-1-lo_isgame_list[::-1].index(True)
                            for linfo in today_lofield_info:
                                lteams = linfo['teams']
                                lhome = lteams[home_CONST]
                                laway = lteams[away_CONST]
                                ltfmetrics = fieldmetrics_list[findexerGet(lteams['div_id'])]['tfmetrics']
                                linfo['homelo_count'] = self.getFieldTeamCount(ltfmetrics, lofield_id, lhome)
                                linfo['homehi_count'] = self.getFieldTeamCount(ltfmetrics, hifield_id, lhome)
                                linfo['awaylo_count'] = self.getFieldTeamCount(ltfmetrics, lofield_id, laway)
                                linfo['awayhi_count'] = self.getFieldTeamCount(ltfmetrics, hifield_id, laway)
                                slot = linfo['slot_index']
                                # get cost associated with early/late counters, if any (0 val if not)
                                linfo['el_cost'] = self.getELcost_by_slot(slot, lteams, lo_lastTrue_slot)
                                # also get el counters for hifield_id teams - they might be swapped into an el slot
                                linfo['hi_teams_in_cost'] = self.getELcost_by_slot(slot,
                                    hi_teams, lo_lastTrue_slot, incoming=1)
                                # get the cost for the min field teams to swap into the max field slot (incoming)
                                # relevant when the hifield_id slot is an early/late slot
                                # note lastTrue_slot is for hifield_id
                                linfo['hi_slot_el_cost'] = self.getELcost_by_slot(
                                    hi_slot, lteams, lastTrue_slot, incoming=1)
                                # calculate min field teams to swap out from the min field slot to max field slot
                                homeswap_cost = linfo['homelo_count']-linfo['homehi_count']
                                awayswap_cost = linfo['awaylo_count']-linfo['awayhi_count']
                                linfo['fieldswap_cost'] = homeswap_cost + awayswap_cost
                                #***********
                                # Total cost for swapping out lofield_id matches is the sum of
                                # swap out cost for lofield_id matches + early/late cost for min field match -
                                # cost for maxf teams to come into the min field slot -
                                # cost for lofield_id teams to go into max field slot
                                linfo['totalswap_cost'] = balanceweight_CONST*linfo['fieldswap_cost'] + linfo['el_cost'] \
                                  - balanceweight_CONST*linfo['hi_teams_in_cost'] - linfo['hi_slot_el_cost']
                            sorted_lofield_info = sorted(today_lofield_info, key=itemgetter('totalswap_cost'), reverse=True)
                            max_linfo = max(today_lofield_info, key=itemgetter('totalswap_cost'))
                            max_linfo['fieldday_id'] = lo_fieldday_id
                            lo_team_metrics_list.append(max_linfo)
                            gameday_totalcost = {'hi_fieldday_id':hi_fieldday_id,
                                'lo_fieldday_id':lo_fieldday_id,
                                'hi_slot':hi_slot, 'oppteam_id':oppteam_id,
                                'lo_slot':max_linfo['slot_index'],
                                'lo_teams':max_linfo['teams'],
                                'lo_lastTrue_slot':lo_lastTrue_slot,
                                'hi_lastTrue_slot':lastTrue_slot,
                                'total_cost':max_linfo['totalswap_cost']+hi_team_metrics['hi_total_cost']}
                            gameday_totalcost_list.append(gameday_totalcost)
                            #logging.debug('ftscheduler:refieldbalance: lofield_info=%s', today_lofield_info)
                            #logging.debug('ftscheduler:refieldbalance: sorted lofield_id=%s', today_lofield_info)
                            logging.debug('ftscheduler:refieldbalance: max lofield_id=%s', max_linfo)
                            logging.debug('ftscheduler:refieldbalance: totalcost=%s', gameday_totalcost)
                    # ******
                    # maximize cost by just taking max of total_cost on list
                    max_totalcost = max(gameday_totalcost_list, key=itemgetter('total_cost'))
                    max_hi_fieldday_id = max_totalcost['hi_fieldday_id']
                    max_lo_fieldday_id = max_totalcost['lo_fieldday_id']
                    max_oppteam_id = max_totalcost['oppteam_id']
                    max_hi_slot = max_totalcost['hi_slot']
                    max_lo_teams = max_totalcost['lo_teams']
                    max_lo_div_id = max_lo_teams['div_id']
                    max_lo_home_id = max_lo_teams[home_CONST]
                    max_lo_away_id = max_lo_teams[away_CONST]
                    max_lo_slot = max_totalcost['lo_slot']
                    max_lo_lastTrue_slot = max_totalcost['lo_lastTrue_slot']
                    max_hi_lastTrue_slot = max_totalcost['hi_lastTrue_slot']
                    logging.debug('ftscheduler:refieldbalance: totalcost_list=%s', gameday_totalcost_list)
                    logging.debug('ftscheduler:refieldbalance: maximum cost info=%s', max_totalcost)

                    logging.debug('ftscheduler:refieldbalance: swapping div=%d team=%d playing opponent=%d on %s hifieldday=%d to lofieldday=%d from slot=%d field=%d',
                        div_id, team_id, max_oppteam_id, common_date,
                        max_hi_fieldday_id,
                        max_lo_fieldday_id, max_hi_slot, hifield_id)
                    logging.debug('ftscheduler:refieldbalance: swap with match div=%d, home=%d away=%d, slot=%d field=%d',
                        max_lo_div_id, max_lo_home_id, max_lo_away_id,
                        max_lo_slot, lofield_id)
                    # ready to swap matches
                    hi_sstatus_list = hi_ftstatus_list[max_hi_fieldday_id-1]['sstatus_list']
                    lo_sstatus_list = lo_ftstatus_list[max_lo_fieldday_id-1]['sstatus_list']
                    hi_teams = hi_sstatus_list[max_hi_slot]['teams']
                    lo_teams = lo_sstatus_list[max_lo_slot]['teams']
                    logging.debug('teams check only before swap maxf=%s minf=%s',
                        hi_sstatus_list[max_hi_slot],
                        lo_sstatus_list[max_lo_slot])
                    hi_sstatus_list[max_hi_slot]['teams'] = lo_teams
                    lo_sstatus_list[max_lo_slot]['teams'] = hi_teams
                    logging.debug('teams check only after swap maxf=%s minf=%s',
                        hi_sstatus_list[max_hi_slot],
                        lo_sstatus_list[max_lo_slot])
                    # increment/decrement fieldmetrics
                    # maxf teams moves out of hifield_id, so decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, hifield_id, hi_teams,
                                            increment=False)
                    # maxf teams moves into lofield_id, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, lofield_id, hi_teams,
                                            increment=True)
                    # minf teams moves out of lofield_id, decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, lofield_id, lo_teams,
                                            increment=False)
                    # minf teams moves into hifield_id, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet, hifield_id, lo_teams,
                                            increment=True)
                    # next adjust EL counters for maxf and minfteams
                    self.updateSlotELCounters(max_hi_slot, max_lo_slot, hi_teams, lo_teams,
                                              lastTrue_slot1 = max_hi_lastTrue_slot,
                                              lastTrue_slot2 = max_lo_lastTrue_slot)
                #team_id += 1
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


    def shiftFSstatus_list(self, field_id, first_pos, fieldday_id):
        ''' shift self.fieldstatus_list struct for a given field and fieldday_id when a new match
        is scheduled for slot 0 '''
        # ref http://stackoverflow.com/questions/522372/finding-first-and-last-index-of-some-value-in-a-list-in-python
        fieldstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
        slotstatus_list = fieldstatus_list['slotstatus_list']
        rg_index = fieldday_id-1
        gameday_list = slotstatus_list[rg_index]['sstatus_list']
        isgame_list = [x['isgame'] for x in gameday_list]
        #firstTrue = isgame_list.index(True)
        #if firstTrue != 0:
        #    return False
        # check to make sure that the first slot to shift has a game scheduled
        if not isgame_list[first_pos]:
            logging.error("ftscheduler:shiftFSstatus: field=%d status shows slot=%d has no game",
                          field_id, first_pos)
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

    def generateSchedule(self, totalmatch_tuple):
        totalmatch_list = totalmatch_tuple.dict_list
        totalmatch_indexerGet = totalmatch_tuple.indexerGet
        self.checkFieldAvailability(totalmatch_tuple);
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in totalmatch_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        # indexer below is used to protect against list of dictionaries that are not ordered according to id,
        # though it is a protective measure, as the list should be ordered with the id.
        #REDO below - we may have to delete current game schedule collection, once we get the name
        # drop only the game schedule documents in the collection - NOT the
        # sched_type and other metadata parameters stored in the collection
        self.dbinterface.dropgame_docs()  # drop current schedule collection
        # used for calaculating time balancing metrics
        ew_list_indexer = getDivFieldEdgeWeight_list(self.divinfo_tuple,
            self.fieldinfo_list)
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
            divtotal_el_list = []
            matchlist_len_list = []
            # take one of those connected divisions and iterate through each division
            for div_id in connected_div_list:
                divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
                divfield_list = divinfo['divfield_list']
                totalteams = divinfo['totalteams']
                div_totalgamedays = divinfo['totalgamedays']
                fset.update(divfield_list)  #incremental union to set of shareable fields
                # http://docs.python.org/2/library/datetime.html#timedelta-objects
                # see also python-in-nutshell
                # convert gameinterval into datetime.timedelta object
                ginterval = divinfo['gameinterval']
                gameinterval_dict[div_id] = timedelta(0,0,0,0,ginterval)
                # get match list for indexed division
                divmatch_dict = totalmatch_list[totalmatch_indexerGet(div_id)]
                # submatch_list is a subset of total_match_list corresponding to
                # connected_div_list
                submatch_list.append(divmatch_dict)
                # calculate number of rounds (gameslots) for the division
                # amongst connected divisions and add to list
                matchlist_len_list.append(len(divmatch_dict['match_list']))
                # describe target fair field usage cout
                divfield_num = len(divfield_list)
                # get number of games scheduled for each team in dvision
                numgames_list = divmatch_dict['numgames_list']
                logging.debug("divsion=%d numgames_list=%s",div_id,numgames_list)
                # for each team, number of games targeted for each field.
                # similar to homeaway balancing number can be scalar (if #teams/#fields is mod 0)
                # or it can be a two element range (floor(#teams/#fields), same floor+1)
                # the target number of games per fields is the same for each field
                # used for field balancing
                numgamesperfield_list = [[n/divfield_num]
                                         if n%divfield_num==0 else [n/divfield_num,n/divfield_num+1]
                                         for n in numgames_list]
                targetfieldcount_list.append({'div_id':div_id, 'targetperfield':numgamesperfield_list})
                fmetrics_list = [{'field_id':x, 'count':0} for x in divfield_list]
                # note below totalteams*[fmetrics_list] only does a shallow copy; use deepcopy
                tfmetrics_list = [deepcopy(fmetrics_list) for i in range(totalteams)]
                fieldmetrics_list.append({'div_id':div_id, 'tfmetrics':tfmetrics_list})
                # metrics and counters for time balancing:
                # expected total fair share of number of early OR late games for each division
                # eff_edgeweight represents 'fair share' of fields
                # factor of 2 comes in because each time slots gets credited to two teams
                # (home and away)
                ew_list = ew_list_indexer.dict_list
                ew_indexerGet = ew_list_indexer.indexerGet
                # NOTE: review computation for divtarget_el for cases where
                # there are multiple gameday availabilities for each round_id
                # for example, if the matches spill over into the second (or later)
                # or later gamedays within the same round_id, should there be
                # credit towards satisfying early/late target counters?
                divtarget_el = 2*div_totalgamedays*ew_list[ew_indexerGet(div_id)]['prodratio']
                # per team fair share of early or late time slots
                teamtarget_el = int(ceil(divtarget_el/totalteams))  # float value
                # calculate each team's target share of early and late games
                earlylate_list = [{'early':teamtarget_el, 'late':teamtarget_el} for i in range(totalteams)]
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
                counter_list = [{'early':0, 'late':0} for i in range(totalteams)]
                self.current_earlylate_list.append({'div_id':div_id, 'counter_list':counter_list})
                # init time gap list element for current div
                # 'last_day' is last gameday, 'last_time' is last gametime
                self.timegap_list.extend([{'div_id':div_id,
                    'last_date':_absolute_earliest_date,
                    'last_endtime':-1, 'team_id':x}
                    for x in range(1, totalteams+1)])
            logging.debug('ftscheduler: target num games per fields=%s',targetfieldcount_list)
            logging.debug('ftscheduler: target early late games=%s divtotal target=%s',
                          self.target_earlylate_list, divtotal_el_list)
            # we are assuming still below that all fields in fset are shared by the field-sharing
            # divisions, i.e. we are not sufficiently handing cases where div1 uses fields [1,2]
            # and div2 is using fields[2,3] (field 2 is shared but not 1 and 3)

            fieldmetrics_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(fieldmetrics_list)).get(x)
            divtotalel_indexer =  dict((p['div_id'],i) for i,p in enumerate(divtotal_el_list))
            self.cel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.current_earlylate_list)).get(x)
            self.tel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.target_earlylate_list)).get(x)
            # gapindexerMatch must have a (div_id, team_id) tuple passed to it
            # gapindexerMatch returns a list, with technically more than one
            # element, but in this class we can assume the list only has a single
            # element so to get the scalar we can always do a [0] on the returned list
            self.timegap_indexerMatch = lambda x: [i for i,p in
                enumerate(self.timegap_list)
                if p['div_id'] == x[0] and p['team_id']==x[1]]
            field_list = list(fset)
            # endtime_list is a list of two-tuples, where t[0] = field_id and
            # t[1] is the end time for the field
            # if endtimes vary enough that it is best to re-calculate for each round,
            # then move determination of endtime_list into to the for round_id loop
            endtime_list = [(f,
                parser.parse(self.fieldinfo_list[self.fieldinfo_indexerGet(f)]['end_time'])) for f in field_list]
            # get the max endtime from all fields
            # Note that we want endtime_list to have two-tuples as elements as
            # endtime_list will be used by other functions where the field_id info
            # will be useful
            # convert to time obj from datetime obj
            latest_endtime = max(endtime_list, key=itemgetter(1))[1]
            commondates_list = self.find_commondates(field_list)
            # use generator list comprehenshion to calcuate sum of required and available fieldslots
            # http://www.python.org/dev/peps/pep-0289/
            # compute number of required gameslots to cover a single round of
            # matches generated by the match generator
            requiredslots_num = sum(totalmatch_list[totalmatch_indexerGet(d)]['gameslots_perround_num']
                for d in connected_div_list)
            for round_id in range(1,max(matchlist_len_list)+1):
                # counters below count how many time each field is used for every gameday
                # reset for each round/gameday
                rd_fieldcount_list = [{'field_id':y, 'count':0} for y in fset]
                rd_fieldcount_indexerGet =  lambda x: dict((p['field_id'],i) for i,p in enumerate(rd_fieldcount_list)).get(x)
                # create combined list of matches so that it can be passed to the multiplexing
                # function 'roundrobin' below
                combined_match_list = []
                for div_dict in submatch_list:
                    divmatch_list = div_dict['match_list']
                    matchlist_indexerGet = lambda x: dict((p['round_id'],i) for i,p in enumerate(divmatch_list)).get(x)
                    rindex = matchlist_indexerGet(round_id)
                    if rindex is not None:
                        div_id = div_dict['div_id']
                        match_list = divmatch_list[rindex]
                        game_list = match_list[game_team_CONST]
                        round_match_list = []
                        for game in game_list:
                            round_match_list.append({'div_id':div_id, 'game':game,
                                'round_id':round_id,
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
                    teamfieldmetrics_list = fieldmetrics_list[fieldmetrics_indexerGet(div_id)]['tfmetrics']
                    gameinterval = rrgame['gameinterval']

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
                    # get the min and max # days that each team should have between
                    # games (set for div_id in UI)
                    mingap_days = self.divinfo_list[self.divinfo_indexerGet(div_id)]['mingap_days']
                    maxgap_days = self.divinfo_list[self.divinfo_indexerGet(div_id)]['maxgap_days']
                    diffgap_days_td = timedelta(maxgap_days - mingap_days)
                    nextmin_datetime = self.getcandidate_daytime(div_id, home_id,
                        away_id, latest_endtime-gameinterval, mingap_days)
                    # get full list of fieldday_id, calendardates that correspond
                    # to min and max nextmin/nextmax datestimes that will bound the
                    # search for fields during current round
                    minmaxdate_tuple = self.getminmaxdate_tuple(nextmin_datetime,
                        diffgap_days_td, field_list)
                    minmaxdate_list = minmaxdate_tuple.dict_list
                    minmaxdate_indexerGet = minmaxdate_tuple.indexerGet
                    logging.debug("----------------------")
                    logging.debug("ftscheduler: rrgenobj loop div=%d round_id=%d home=%d away=%d",
                                  div_id, round_id, home_id, away_id)
                    logging.debug("early late hometarget=%s awaytarget=%s homecurrent=%s awaycurrent=%s",
                                  home_targetel_dict, away_targetel_dict, home_currentel_dict, away_currentel_dict)
                    logging.debug("next min datetime %s",nextmin_datetime)
                    logging.debug("ftscheduler:generate: fieldlist=%s minmaxdate_list=%s",
                        field_list, minmaxdate_list)
                    # get list of fields/fieldday_ids sorted by date
                    # each element is a dict with
                    # {'date':x,'datefield_list':[{'field_id':y, fieldday_id:z}...]}
                    # entries
                    datesortedfield_list = self.datesort_fields(minmaxdate_list,
                        minmaxdate_indexerGet, field_list)
                    # get homefield_list for both home and away teams
                    hf_list = []
                    for idtype in [home_id, away_id]:
                        tmindex = self.tminfo_indexerGet((div_id, idtype))
                        # remember append order follows idtype iteration
                        hf_list.append(self.tminfo_list[tmindex]['af_list'] if tmindex is not None else None)
                    # next get list of fields sorted by sumcount priorities
                    # each elem is a dict with
                    # {'sumcount':x, 'field_list'[x,y,z...]}
                    # sumcount-based optimization is driven by field balancing
                    # criteria
                    sumsortedfield_list = self.findMinimumCountField(home_fieldmetrics_list, away_fieldmetrics_list,
                        rd_fieldcount_list, requiredslots_num, hf_list[0],
                        hf_list[1])
                    if not sumsortedfield_list:
                        raise FieldAvailabilityError(div_id)
                    logging.debug("rrgenobj while True loop:")
                    logging.debug("divid=%d round_id=%d home=%d away=%d homemetrics=%s awaymetrics=%s",
                        div_id, round_id, home_id, away_id, home_fieldmetrics_list,
                        away_fieldmetrics_list)
                    logging.debug("datesortedlist=%s", datesortedfield_list)
                    logging.debug("sumsortedlist=%s", sumsortedfield_list)
                    # *********************************
                    # Here we are assuming that minimum date has priority
                    # if prioritization has a different structure, reorder the
                    # logic governing datesortedfield, sumsortedfield, and prioritizefield below
                    for dsfield_dict in datesortedfield_list:
                        dategame_date = dsfield_dict['date']
                        datefield_list = dsfield_dict['datefield_list']
                        if len(datefield_list) > 1:
                            # if there are two or more fields that can be assigned
                            # for the given date, then find the priority amongst
                            # those fields
                            prioritized_list = self.prioritizefield_list(datefield_list, sumsortedfield_list,key="sumcount")
                            for p_dict in prioritized_list:
                                # go through the ordered list of fields
                                field_id = p_dict['field_id']
                                fieldday_id = p_dict['fieldday_id']
                                slot_index = self.findconfirm_slot(field_id,
                                    fieldday_id, home_currentel_dict,
                                    away_currentel_dict, el_state, EL_enum)
                                if slot_index is not None:
                                    break
                            else:
                                # iterated on the next datesortedfield_list entry
                                continue
                            break
                        else:
                            df_dict = datefield_list[0]
                            field_id = df_dict['field_id']
                            fieldday_id = df_dict['fieldday_id']
                            slot_index = self.findconfirm_slot(field_id,
                                fieldday_id, home_currentel_dict,
                                away_currentel_dict, el_state, EL_enum)
                            if slot_index is not None:
                                break
                    else:
                        if slot_index is None:
                            # exhaused candidate field and dates, raise error
                            raise FieldAvailabilityError(div_id)
                    # these get exected after while True breaks
                    logging.debug("ftscheduler: after timeslot=%d assign div=%d round_id=%d home_id=%d away_id=%d",
                                  slot_index, div_id, round_id, home_id, away_id)
                    logging.debug("ftscheduler: assign to field=%d slotind=%d home_currentel=%s away_currentel=%s",
                                  field_id, slot_index, home_currentel_dict, away_currentel_dict)
                    fieldstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
                    slotstatus_list = fieldstatus_list['slotstatus_list']
                    fieldday_index = fieldday_id-1
                    slotstatus_dict = slotstatus_list[fieldday_index]
                    game_date = slotstatus_dict['game_date']
                    computedgame_date = self.mapfieldday_datetime(field_id, fieldday_id)
                    selected_ftstatus = slotstatus_dict['sstatus_list'][slot_index]
                    selected_ftstatus['isgame'] = True
                    selected_ftstatus['teams'] = {'div_id': div_id, home_CONST:home_id, away_CONST:away_id}
                    gametime = selected_ftstatus['start_time']
                    if game_date != computedgame_date:
                        raise CodeLogicError("ftscheduler:generate: sstatus game_date %s does not match w computed game_date %s" % (game_date, computedgame_date))
                    else:
                        logging.debug("ftscheduler:generate: game played date %s time %s", game_date, gametime.time())
                    home_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list))
                    away_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list))
                    home_fieldmetrics_list[home_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    away_fieldmetrics_list[away_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    rd_fieldcount_list[rd_fieldcount_indexerGet(field_id)]['count'] += 1
                    self.updatetimegap_list(div_id, home_id, away_id, game_date,
                        gametime+gameinterval)
                    div = self.divinfo_list[self.divinfo_indexerGet(div_id)]
                    logging.info("div=%s%s home=%d away=%d round_id=%d, date=%s fieldday_id=%d field=%d gametime=%s slotindex=%d",
                        div['div_age'], div['div_gen'], home_id, away_id, round_id,
                        game_date, fieldday_id, field_id, gametime.time(),
                        slot_index)
                    logging.info("-----to next game------")
                logging.debug("ftscheduler: divlist=%s end of round=%d rd_fieldcount_list=%s",
                              connected_div_list, round_id, rd_fieldcount_list)
            self.ReFieldBalanceIteration(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
            # now work on time balanceing
            self.ReTimeBalance(fset, connected_div_list)
            self.ManualSwapTeams(fset, connected_div_list)
            if self.prefinfo_list:
                constraint_status_list = self.ProcessConstraints(fset, connected_div_list)
                self.pdbinterface.write_constraint_status(constraint_status_list)
            # read from memory and store in db
            for field_id in fset:
                fieldday_id = 1
                for fieldday_id, slotstatus_list in enumerate(self.fieldstatus_list[self.fstatus_indexerGet(field_id)]['slotstatus_list'], start=1):
                    if not slotstatus_list:
                        # if fieldday is closed for that field, continue to next fieldday
                        continue
                    game_date = slotstatus_list['game_date']
                    for match in slotstatus_list['sstatus_list']:
                        if match['isgame']:
                            start_time = match['start_time']
                            teams = match['teams']
                            div_id = teams['div_id']
                            home_id = teams[home_CONST]
                            away_id = teams[away_CONST]
                            #div = getAgeGenderDivision(div_id)
                            div = self.divinfo_list[self.divinfo_indexerGet(div_id)]
                            self.dbinterface.insertGameData(age=div['div_age'],
                                gen=div['div_gen'], fieldday_id=fieldday_id,
                                #game_date_str=game_date.strftime(date_format_CONST),
                                #start_time_str=gametime.strftime(time_format_CONST),
                                game_date=game_date, start_time=start_time,
                                venue=field_id, home=home_id, away=away_id)
        self.dbinterface.setsched_status()
        return True  # for dbstatus to be returned to client
        # executes after entire schedule for all divisions is generated
        #self.compactTimeSchedule()

    def findconfirm_slot(self, field_id, fieldday_id, home_currentel_dict, away_currentel_dict, el_state, EL_enum):
        ''' Confirm if the candidate field_id and fieldday_id/date can be used
        to assign a game by checking fieldseason status list. Note instead
        of implementing an if..else if...else structure, code implemented with
        series of if .. return as there are cases when an inner if fails, other
        subsequent tests should be performed'''
        fstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
        fday_index = fieldday_id-1
        sstatus_list = fstatus_list['slotstatus_list'][fday_index]['sstatus_list']
        # first create simple array of isgame statuses for the given slotstatus_list
        # if it is all True then it is not usable
        isgame_list = [x['isgame'] for x in sstatus_list]
        if all(isgame_list):
            # not usable as games are scheduled in every slot, return False so that
            # calling function can find another alternate candidate field_id/fieldday
            return None
        # as long as we have one Falso in the isgame_list for current field_id,
        # continue processing
        if all_value(isgame_list, False):
            # if there are no games scheduled for the field, assign to first slot
            # and update both early/late counters by giving credit to both
            slot_index = 0
            self.incrementEL_counters(home_currentel_dict, away_currentel_dict,
                'early')
            self.incrementEL_counters(home_currentel_dict, away_currentel_dict,
                'late')
            return slot_index
        if el_state & EL_enum.EARLY_TEAM_NOTMET and el_state & EL_enum.EARLY_DIVTOTAL_NOTMET:
            # if we have not met the early slot criteria, try to fill slot 0
            if not isgame_list[0]:
                # if no game scheduled in first slot, schedule it
                slot_index = firstslot_CONST
                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                return slot_index
            else:
                # if slot 0 is not open, first see if it makes sense to shift other
                # scheduled slots to open up slot 0
                # see if it makes sense to push out the current slot-0-scheduled
                # match
                # find out div and teams that are already scheduled for slot 0
                # since slot should be scheduled, a 'teams'
                # key/value pair should ahve already been added
                match_list = [{'field_id':field_id,
                    'match':sstatus_list[0]['teams'], 'newslot':0}]
                fieldslot_tuple = self.compareCounterToTarget(match_list, 'early')
                if fieldslot_tuple:
                    # ok we can shift
                    # if the current home and away early counts are both greater
                    # than the target amount, they can afford to be bumped out the
                    # earliest slots; current match will take its place at slot 0
                    slot_index = fieldslot_tuple.slot_index # should be slot 0
                    self.shiftFSstatus_list(field_id, slot_index, fieldday_id)
                    self.incrementEL_counters(home_currentel_dict,
                        away_currentel_dict, 'early')
                    return slot_index
        firstopen_index = isgame_list.index(False)
        if el_state & EL_enum.LATE_TEAM_NOTMET and el_state & EL_enum.LATE_DIVTOTAL_NOTMET:
            # if last slot should be scheduled, then find the last open slot in the currently scheduled set
            # and insert this current match at that open slot - note that we are not necessarily
            # scheduling at the very last slot of the day
            # Note to prevent index value exceptions, don't add a list element if all of the 1-element list
            # is true or the last element in the 1-element list is True (game already scheduled in the very last slot)
            # note on handling exceptions within list comprehension - basically can't do
            # http://stackoverflow.com/questions/1528237/how-can-i-handle-exceptions-in-a-list-comprehension-in-python
            # Note above comments taken from the multiple fieldcand_list case which
            # does not exist in the current code and comments may no longer be
            # applicable.
            # see if there is only one game scheduled so far (assumed that
            # game is scheduledin slot 0, which should always be the case)
            if firstopen_index == 1:
                slot_index = 1
                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                self.findTeamsDecrementEL_counters(field_id, 0, 'late', fieldday_id)
                return slot_index
            # ok there are no fields with only one game scheduled - next what we are going to do now is to look
            # at the fields and see if there are any last game matches that can afford to not be the last game
            # anymore.  This is done by looking at the late counters and see if there any over the target count.
            # Both home and away counters need to be over the target.
            # dict 'field_id' is field_id, 'match' is the match info for the already-scheduled slot
            # new slot is the current open slot
            # see if the last game can afford to not be the last game
            # anymore - do this by looking at the late counters and seeing
            # if it is over the target value (both home and away)
            match_list = [{'field_id':field_id,
                'match':sstatus_list[firstopen_index-1]['teams'],
                'newslot':firstopen_index}]
            fieldslot_tuple = self.compareCounterToTarget(match_list, 'late')
            if fieldslot_tuple:
                # if the current home and away late counts are both greater than
                # the target amount, they can afford to have the scheduled spot take up the last slot
                # fyi no shifting is necessary for 'late' (unlike for 'early' where shifting is needed when slot 0 is taken up)
                slot_index = fieldslot_tuple.slot_index
                # increment for current home and away teams which will take last slot
                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                return slot_index
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
        # for EL_enum 'normal' cases, see if it makes sense to take over first or last slot anyways
        firstlastmatch_list = [{'field_id':field_id,
            'firstmatch':sstatus_list[0]['teams'],
            'firstmatch_newslot':0,
            'lastmatch':sstatus_list[firstopen_index-1]['teams'],
            'lastmatch_newslot':firstopen_index}]
        fieldslotELtype_tuple = self.findBestSlot(firstlastmatch_list)
        if fieldslotELtype_tuple:
            slotfield_id = fieldslotELtype_tuple.field_id
            if slotfield_id != field_id:
                raise CodeLogicError("ftscheduler:findconfirm_slot: field_id inconsistency slotfield=%d field_id=%d" %
                    (slotfield_id, field_id))
            slot_index = fieldslotELtype_tuple.slot_index
            el_str = fieldslotELtype_tuple.el_str
            if slot_index == 0 and el_str == 'early':
                # shift the current scheduled games to the right one spot
                self.shiftFSstatus_list(field_id, slot_index,
                    fieldday_id)
            elif (slot_index == 0 and el_str != 'early') or (slot_index != 0 and el_str == 'early'):
                raise CodeLogicError("ftscheduler:findBestSlot slot_index el_str logic error")
            # increment for current home and away teams which will take last slot
            self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_str)
            return slot_index
        else:
            # for all other cases, schedule not at first available slot, but take the last
            # scheduled slot - and shift the currently scheduled last slot over to the right one
            slot_index = firstopen_index-1
            self.shiftFSstatus_list(field_id, slot_index,
                fieldday_id)
            if slot_index == 0:
                # if we are inserting into slot0, then update appropriate EL counters
                self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                self.findTeamsDecrementEL_counters(field_id,
                    1, 'early', fieldday_id)
            return slot_index

    def updatetimegap_list(self, div_id, home, away, game_date, endtime):
        ''' update self.timegap_list entries with latest scheduled games '''
        for team in (home, away):
            teamgap_dict = self.timegap_list[self.timegap_indexerMatch((div_id, team))[0]]
            # game_date comes in as a datetime obj so covert to dateobj
            teamgap_dict['last_date'] = game_date.date()
            teamgap_dict['last_endtime'] = endtime.time()

    def getcandidate_daytime(self, div_id, home, away, latest_starttime, mingap_days):
        ''' get next earliest potential calendar date and time to schedule a game.
        Satisfies gaptime requirements.  Note calculations are based on raw
        calendar dates; Actual scheduling dates based on real field availability is
        done outside of this method.'''
        homegap_dict = self.timegap_list[self.timegap_indexerMatch((div_id, home))[0]]
        awaygap_dict = self.timegap_list[self.timegap_indexerMatch((div_id, away))[0]]
        homegap_gameday = homegap_dict['last_date']
        awaygap_gameday = awaygap_dict['last_date']
        homegap_end = homegap_dict['last_endtime']
        awaygap_end = awaygap_dict['last_endtime']
        if homegap_gameday == awaygap_gameday:
            maxgap_gameday = homegap_gameday
            maxgap_end = max(homegap_end, awaygap_end)
        elif homegap_gameday > awaygap_gameday:
            maxgap_gameday = homegap_gameday
            maxgap_end = homegap_end
        else:
            maxgap_gameday = awaygap_gameday
            maxgap_end = awaygap_end
        if maxgap_gameday == _absolute_earliest_date:
            # initial condition
            next_start = _absolute_earliest_time
            # get equivalent datetime object
            nextmin_datetime = datetime.combine(maxgap_gameday, next_start)
            # nextmax_datetime is later calculated once the field list is known
        else:
            maxgap_datetime = datetime.combine(maxgap_gameday, maxgap_end)
            # calculate earliest datetime that satisfies the minimum timegap
            # between games
            # NOTE: for now assume unit of gap to be days
            nextmin_datetime = maxgap_datetime + timedelta(days=mingap_days)
            if nextmin_datetime.time() > latest_starttime.time():
                # get time from the next_datetime - if it exceeds the latest allowable
                # time, increment date and set time to earliest time
                next_gameday = nextmin_datetime.date() + timedelta(days=1)
                next_start = _absolute_earliest_time
                nextmin_datetime = datetime.combine(next_gameday, next_start)
            # get the latest allowable date/time to have the next scheduled game
            # we have to set a max so that the algorithm does not indefinitely look
            # for dates to schedule a game; if the max is reached and no game can be
            # scheduled, then there is field resource problem.
            # CHANGE: nextmax_datetime is calculated only After a real fieldday
            # date is found out
        return nextmin_datetime

    def datesort_fields(self, minmaxdate_list, minmaxdate_indexerGet, field_list):
        ''' sort and group fields by calendar date; sort list by calendar date
        before returning'''
        date_list = list(set([x['date'] for f in field_list for x in minmaxdate_list[minmaxdate_indexerGet(f)]['fielddate_list']]))
        # initialize return list
        datesortedfield_list = [{'date':x, 'datefield_list':[]} for x in date_list]
        dsfield_indexerGet = lambda x: dict((p['date'],i) for i,p in enumerate(datesortedfield_list)).get(x)
        minmaxdate_indexerMatch = lambda x: [i for i,p in
            enumerate(minmaxdate_list) if p['min_date'] == x]
        for field_id in field_list:
            fielddate_list = minmaxdate_list[minmaxdate_indexerGet(field_id)]['fielddate_list']
            for fielddate_dict in fielddate_list:
                dsfield_dict = datesortedfield_list[dsfield_indexerGet(fielddate_dict['date'])]
                dsfield_dict['datefield_list'].append({'field_id':field_id,
                    'fieldday_id':fielddate_dict['fieldday_id']})
        # sort according to date field
        datesortedfield_list.sort(key=itemgetter('date'))
        return datesortedfield_list

    def prioritizefield_list(self, datefield_list, sortedinput_list, key):
        ''' Prioritize fields in list as dictated by prioritization list passed
        in as second parameter'''
        key_list = sorted([x[key] for x in sortedinput_list])
        si_indexerGet = lambda x: dict((p[key],i) for i,p in enumerate(sortedinput_list)).get(x)
        prioritizednested_list = [[x for x in datefield_list if x['field_id'] in sortedinput_list[si_indexerGet(y)]['field_list']] for y in key_list]
        # http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python for flattening nested lists
        prioritized_list = list(chain.from_iterable(prioritizednested_list))
        return prioritized_list

    def getminmaxdate_tuple(self, nextmin_datetime, diffgap_days_td, field_list):
        ''' Given nextmin_datetime calculated by getcandidate_daytime, along with
        the required gap between max and mintimes, and the field_list, calculate
        fieldday_id and calendar dates that fall on potentially available days on
        a given field (specified by fieldinfo data). Calculate both min and max
        dates and fieldday_id's that bound the search for scheduling days for a
        specific field.
        Calculate latest date that search for a field should iterate to; mindate is
        real field date calculate latest date for stopping search, and then find
        field date that is equal to or latest date that is earlier than that date'''
        minmaxdate_list = []
        for field_id in field_list:
            minfieldday_id, min_date = self.mapdatetime_fieldday(field_id,
                nextmin_datetime, key='min')
            nextmax_datetime = min_date + diffgap_days_td
            maxfieldday_id, max_date = self.mapdatetime_fieldday(field_id,
                nextmax_datetime, key='max')
            fielddate_list = [{'fieldday_id':x,
                'date':self.mapfieldday_datetime(field_id, x)}
                for x in range(minfieldday_id, maxfieldday_id+1)]
            minmaxdate_dict = {'field_id':field_id,
                'fielddate_list':fielddate_list,
                'minfieldday_id':minfieldday_id, 'min_date':min_date,
                'maxfieldday_id':maxfieldday_id, 'max_date':max_date}
            minmaxdate_list.append(minmaxdate_dict)
        minmaxdate_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(minmaxdate_list)).get(x)
        return _List_Indexer(minmaxdate_list, minmaxdate_indexerGet)

    def mapdatetime_fieldday(self, field_id, dt_obj, key):
        ''' Map datetime date to fieldday_id as defined by the calendarmap_list
        for the field_id '''
        fieldinfo_list = self.fieldinfo_list[self.fieldinfo_indexerGet(field_id)]
        calendarmap_list = fieldinfo_list['calendarmap_list']
        date_list = [x['date'].date() for x in calendarmap_list]
        dt_date = dt_obj.date()
        if key == 'min':
            # find earliest date that is equal to after the reference dt_date
            (match_index, match_date) = find_ge(date_list, dt_date)
        else:
            # find latest date that is equal to or before the the reference date
            (match_index, match_date) = find_le(date_list, dt_date)
        match_dict = calendarmap_list[match_index]
        return (match_dict['fieldday_id'], match_dict['date'])

    def mapfieldday_datetime(self, field_id, fieldday_id):
        "Map fieldday_id to date as expressed in datetime obj"
        fieldinfo_list = self.fieldinfo_list[self.fieldinfo_indexerGet(field_id)]
        calendarmap_list = fieldinfo_list['calendarmap_list']
        calendarmap_indexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(calendarmap_list)).get(x)
        return calendarmap_list[calendarmap_indexerGet(fieldday_id)]['date']

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
                        fslot_status = self.fieldstatus_list[self.fstatus_indexerGet(f)]['slotstatus_list']
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



    def ReFieldBalanceIteration(self, connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet, commondates_list):
        old_balcount_list = self.CountFieldBalance(connected_div_list,
            fieldmetrics_list, fieldmetrics_indexerGet)
        old_bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(old_balcount_list)).get(x)
        iteration_count = 1
        logging.debug("ftscheduler:refieldbalance: iteration=%d 1st balance count=%s", iteration_count,
                      old_balcount_list)
        while True:
            rebalance_count = self.ReFieldBalance(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
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


    def shiftGameDaySlots(self, fieldstatus_round, isgame_list, field_id, fieldday_id, src_begin, dst_begin, shift_len):
        ''' shift gameday timeslots '''
        logging.debug("ftscheduler:compaction:shiftGameDayslots isgamelist=%s, field=%d gameday=%d src_begin=%d dst_begin=%d len=%d",
                      isgame_list, field_id, fieldday_id, src_begin, dst_begin, shift_len)
        src_end = src_begin + shift_len
        dst_end = dst_begin + shift_len
        for i,j in zip(range(src_begin, src_end), range(dst_begin, dst_end)):
            srcslot = fieldstatus_round[i]
            dstslot = fieldstatus_round[j]
            if srcslot['isgame']:
                # if a game exists, shift to new time slot, and update db doc entry
                dstslot['isgame'] = srcslot['isgame']
                # if dstslot has a game (True field), then write to db
                self.dbinterface.updateGameTime(field_id, fieldday_id,
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
                    self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, fieldday_id,
                                           src_begin=newsrc_begin, dst_begin=newdst_begin, shift_len=newshift_length)
                    for k in range(newdst_begin+newshift_length, dst_end):
                        fieldstatus_round[k]['isgame'] = False
                finally:
                    break

    def findFieldGamedayLastTrueSlot(self, field_id, fieldday_id):
        sstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]['slotstatus_list'][fieldday_id-1]['sstatus_list']
        isgame_list = [x['isgame']  for x in sstatus_list]
        lastslot = len(isgame_list)-1-isgame_list[::-1].index(True)
        return lastslot

    def RecomputeCEL_list(self, fset, div_set):
        ''' recompute current_earlylist_counter structure by going through fieldseasonstatus matrix '''
        for div_id in div_set:
            # first clear counters
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            totalteams = divinfo['totalteams']
            for elcounter in self.current_earlylate_list[self.cel_indexerGet(div_id)]['counter_list']:
                elcounter['early'] = 0
                elcounter['late'] = 0
        for f in fset:
            fslot_status = self.fieldstatus_list[self.fstatus_indexerGet(f)]['slotstatus_list']
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
        constraint_status_list = []
        for div_id in div_set:
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            ginterval = divinfo['gameinterval']
            gameinterval = timedelta(0,0,0,0,ginterval) # to be able to add time - see leaguedivprep fieldseasonstatus

            # get constraints for each div
            divconstraint_list = [self.prefinfo_list[x]
                for x in self.prefinfo_indexerMatch(div_id)]
            if divconstraint_list:
                # each time might have multiple constraints
                # read each constraint and see if any are already met by default
                for constraint in divconstraint_list:
                    cpref_id = constraint['pref_id']
                    cpriority = constraint['priority']
                    cdiv_id = constraint['div_id']
                    cteam_id = constraint['team_id']
                    startafter_str = constraint.get('start_after')
                    startafter_time = parser.parse(startafter_str)
                    endbefore_str = constraint.get('end_before')
                    endbefore_time = parser.parse(endbefore_str)
                    cgame_date = parser.parse(constraint['game_date']).date()
                    break_flag = False
                    swapmatch_list = []
                    for f in fset:
                        # reassign cstartafter_time, cendbefore_time in case  it
                        # was nulled out in previous loop
                        cstartafter_time = startafter_time
                        cendbefore_time = endbefore_time
                        # first get calendarmap_list for the field, and see if there
                        # is an entry for the priority list game_date
                        finfo = self.fieldinfo_list[self.fieldinfo_indexerGet(f)]
                        fstart_time = parser.parse(finfo['start_time'])
                        fend_time = parser.parse(finfo['end_time'])
                        cmap_list = finfo['calendarmap_list']
                        cmap_indexerMatch_list = lambda x: [i for i,p in
                            enumerate(cmap_list) if p['date'].date() == x]
                        cmap_index_list = cmap_indexerMatch_list(cgame_date)
                        if cmap_index_list:
                            # ok we confirmed that the cmap_list has an entry that
                            # matches with the game date entered in the priority
                            # list
                            # we can assume there is only one match
                            cmap_index = cmap_index_list[0]
                            cmap = cmap_list[cmap_index]
                            cmapfieldday_id = cmap['fieldday_id']
                            if 'start_time' in cmap:
                                # if start_time exists in cmap, then it means that
                                # there has been a change applied using calendar UI
                                # and cmap start and end times have precedence over
                                # start and end times passed from the grid table
                                fstart_time = parser.parse(calendarmap['start_time'])
                                fend_time = parser.parse(calendarmap['end_time'])
                            if cstartafter_time <= fstart_time:
                                # if the startafter_time is before the earliest time
                                # for that date, it is equivalent to startafter_time
                                # not existing
                                cstartafter_time = None
                            if cendbefore_time >= fend_time:
                                # similarly if the endbefore time is later than the
                                # latest time on the field, it is the same as the
                                # the endbefore time not defined
                                cendbefore_time = None
                            # we can support two separate continuous segments of desired slots (but not more than two)
                            # define the type of segment basd on presend of start and endtimes and their values
                            # comment visually shows time slots (not position accurate) that will satisfy time constraints
                            segment_type = -1
                            if cstartafter_time and not cendbefore_time:
                                # [------TTTT]
                                segment_type = 0
                            elif not cstartafter_time and cendbefore_time:
                                # [TTTT------]
                                segment_type = 1
                            elif cstartafter_time and cendbefore_time:
                                if cendbefore_time > cstartafter_time:
                                    # [---TTTTTT---]
                                    segment_type = 2
                                elif cendbefore_time < cstartafter_time:
                                    #[TTTT----TTTTT]
                                    segment_type = 3
                                elif cendbefore_time == cstartafter_time:
                                    # [TTTTTTTTTTTT] (no constraint)
                                    logging.debug("ftscheduler:processconstraints: constraint %d is not needed since start_after=end_before",
                                        cpref_id)
                                    continue # go to the next field in fset
                            else:
                                logging.debug("ftscheduler:processconstraints: constraint %d nothing specified",
                                    cpref_id)
                                continue
                            # first
                            # search through each field for the divset to 1)find if team is already scheduled in a desired slot; or
                            # 2) if not, find the list of matches that the team can swap with during that day
                            fstatus = self.fieldstatus_list[self.fstatus_indexerGet(f)]
                            fslots_num = fstatus['daygameslots_num']
                            fsstatus_list =  fstatus['slotstatus_list'][cmapfieldday_id-1]['sstatus_list']
                            # find out slot number that is designated by the 'start_after' constraint
                            firstgame_slot = fsstatus_list[0]
                            if not firstgame_slot or not firstgame_slot['isgame']:
                                raise CodeLogicError("ftscheduler:ProccessContraints: firstgame for div %d, fieldday %d does not exist" % (cdiv_id, cd_fieldday_id))
                            firstgame_time = firstgame_slot['start_time']  # first game time
                            startafter_index = self.mapStartTimeToSlot(cstartafter_time, firstgame_time, gameinterval) if cstartafter_time else None
                            if startafter_index and startafter_index > fslots_num - 1:
                                raise SchedulerConfigurationError("Constraint Configuration Error: Start after time is too late")

                            # -1 return means that the end time is before the end of the first game
                            endbefore_index = self.mapEndTimeToSlot(cendbefore_time, firstgame_time, gameinterval) if cendbefore_time else -2

                            fullindex_list = range(fslots_num)
                            # define range of time slots that satisfy constraints
                            if segment_type == 0:
                                segment_range = range(startafter_index, fslots_num)
                            elif segment_type == 1:
                                segment_range = range(0, endbefore_index+1)
                            elif segment_type == 2:
                                segment_range = range(startafter_index, endbefore_index+1)
                            elif segment_type == 3:
                                segment_range = range(0,endbefore_index+1) + range(startafter_index, fslots_num)
                            else:
                                # ref http://www.diveintopython.net/native_data_types/formatting_strings.html for formatting string
                                raise CodeLogicError("ftscheduler:process constraints - error with segment type, constraint %d" %(cpref_id,))
                            # based on segment range, create list with T/F values - True represents slot that satisfies
                            # time constraint
                            canswapTF_list = [True if x in segment_range else False for x in fullindex_list]
                            #print 'cd id canswap', cpref_id, canswapTF_list
                            for slot_ind, slot_TF in enumerate(canswapTF_list):
                                if slot_TF:
                                    fstatus_slot = fsstatus_list[slot_ind]
                                    # search through gameday slots where game is already scheduled
                                    if fstatus_slot['isgame']:
                                        teams = fstatus_slot['teams']
                                        div_id = teams['div_id']
                                        home = teams[home_CONST]
                                        away = teams[away_CONST]
                                        if div_id == cdiv_id and (home == cteam_id or away == cteam_id):
                                            logging.info("ftscheduler:constraints: ***constraint satisfied with constraint=%d div=%d team=%d gameday=%d",
                                                cpref_id, div_id, cteam_id, cmapfieldday_id)
                                            break_flag = True
                                            break  # from inner for canswapTF_list loop
                                        else:
                                            swapmatch_list.append({'teams':teams,
                                                'slot_index':slot_ind,
                                                'field_id':f,
                                                'fieldday_id':cmapfieldday_id})
                            else:
                                logging.debug("ftscheduler:processconstraints:candidate matches in field=%d constraint=%d for swap %s",
                                              f, cpref_id, swapmatch_list)
                                continue # to next field_id in fset loop
                            break  # from outer for fset loop
                        else:
                            # if calendarmap does not produce a gamedate match
                            continue
                    if break_flag:
                        logging.debug("ftscheduler:processconstraints id %d already satisfied as is", cpref_id)
                        print '*********constraint', cpref_id, 'is already satisfied'
                        constraint_status_list.append({'pref_id':cpref_id,
                            'status':1})
                    else:
                        logging.debug("ftscheduler:processconstraints: constraint id=%d  candidate swap=%s",
                            cpref_id, swapmatch_list)
                        print '####constraint', cpref_id
                        status = self.findMatchSwapForConstraint(fset, cdiv_id, cteam_id, cgame_date, cpriority, swapmatch_list)
                        constraint_status_list.append({'pref_id':cpref_id,
                            'status':status})
        return constraint_status_list

    def findMatchSwapForConstraint(self, fset, div_id, team_id, game_date, priority, swap_list):
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
        fstatus_tuple = self.findFieldSeasonStatusSlot(fset, div_id, team_id,
            game_date)
        refteams = fstatus_tuple.teams
        reffield_id = fstatus_tuple.field_id
        refslot_index = fstatus_tuple.slot_index
        refoppteam_id = fstatus_tuple.oppteam_id
        reffieldday_id = fstatus_tuple.fieldday_id
        lastTrueSlot = self.findFieldGamedayLastTrueSlot(reffield_id,
            reffieldday_id)
        # note we will most likely continue to ignore refoppteam_cost value below as it has no
        # bearing on max operation (same value for all swap candidates)
        if refslot_index == 0:
            refoppteam_cost = self.getSingleTeamELstats(div_id, refoppteam_id, 'early')
        elif refslot_index == lastTrueSlot:
            refoppteam_cost = self.getSingleTeamELstats(div_id,
                refoppteam_id, 'late')
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
        #print 'div team gameday slot field index', div_id, team_id, fieldday_id, refslot_index, reffield_id, samefield_index_list
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
                fsstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(reffield_id)]['slotstatus_list'][reffieldday_id-1]['sstatus_list']
                if fsstatus_list[refslot_index]['teams'] !=  refteams:
                    raise CodeLogicError("ftschedule:findSwapMatchConstraints refslotindex %d does not produce teams %s"
                                         % (refslot_index, refteams))
                max_swap_slot_index = max_swap['slot_index']
                max_swap_teams = max_swap['teams']
                if fsstatus_list[max_swap_slot_index]['teams'] != max_swap_teams:
                    raise CodeLogicError("ftschedule:findSwapMatchConstraints swapslot %d does not produce teams %s"
                                         % (max_swap_slot_index, max_swap_teams))
                fsstatus_list[refslot_index]['teams'], fsstatus_list[max_swap_slot_index]['teams'] = \
                  fsstatus_list[max_swap_slot_index]['teams'], fsstatus_list[refslot_index]['teams']
                logging.debug("ftscheduler:swapmatchconstraints: swapping refslot %d with slot %d, refteams %s with teams %s",
                              refslot_index, max_swap_slot_index, refteams, max_swap_teams)
                print "****swapping refslot %d with slot %d, refteams %s with teams %s" % (refslot_index, max_swap_slot_index, refteams, max_swap_teams)

                self.updateSlotELCounters(refslot_index, max_swap_slot_index, refteams, max_swap_teams,
                                          lastTrueSlot, lastTrueSlot)
                return 1
            else:
                logging.debug("ftscheduler:findMatchSwapConstraints cost list is empty, No Swap")
                print '*** No elements left in cost_list, NONE'
                return 0
        else:
            print '****No options in the same field, returning NONE'
            return 0


    def findFieldSeasonStatusSlot(self, fset, div_id, team_id, game_date):
        break_flag = False
        for f in fset:
            slotstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(f)]['slotstatus_list']
            sindexerGet = lambda x: dict((p['game_date'].date(),i) for i,p in enumerate(slotstatus_list)).get(x)
            fieldday_dict = slotstatus_list[sindexerGet(game_date)]
            fieldday_id = fieldday_dict['fieldday_id']
            sstatus_list = fieldday_dict['sstatus_list']
            for slot_index, sstatus in enumerate(sstatus_list):
                if sstatus['isgame']:
                    teams = sstatus['teams']
                    if teams['div_id'] == div_id and (teams[home_CONST]==team_id or teams[away_CONST]==team_id):
                        oppteam_id = teams[home_CONST] if teams[away_CONST]==team_id else teams[away_CONST]
                        break_flag = True
                        break
            else:
                continue
            break
        if break_flag:
            StatusSlot_tuple = namedtuple('StatusSlot_tuple', 'slot_index field_id oppteam_id teams fieldday_id')
            return StatusSlot_tuple(slot_index, f, oppteam_id, teams, fieldday_id)
        else:
            raise CodeLogicError("constraints: findswapmatch can't find slot for div=%d team=%d gameday=%d" % (div_id, team_id, fieldday_id))

    def compactTimeSchedule(self):
        ''' compact time schedule by identifying scheduling gaps through False statueses in the 'isgame' field '''
        for fieldstatus in self.fieldstatus_list:
            field_id = fieldstatus['field_id']
            fieldday_id = 1
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
                                  field_id, fieldday_id)
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
                                     field_id, fieldday_id)
                        self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, fieldday_id,
                                               src_begin=firstgame_ind, dst_begin=dst_begin, shift_len=shift_length)
                        for i in range(dst_begin+shift_length, fieldstatus_len):
                            fieldstatus_round[i]['isgame'] = False
                    else:
                        # Game in first slot, iterate from this point to find and compact time schedule gaps.
                        try:
                            false_ind = isgame_list.index(False)
                        except ValueError:
                            logging.error("ftscheduler:compaction:field=%d gameday=%d is full", field_id, fieldday_id)
                            # all slots filled w. games, no False state
                            continue
                        else:
                            if false_ind == 0:
                                # this should not happen based on if else
                                raise TimeCompactionError(field_id, fieldday_id)
                            try:
                                true_ind = isgame_list[false_ind:].index(True)
                            except ValueError:
                                logging.error("ftscheduler:compaction:field=%d gameday=%d no more gaps; gameday schedule is continuous and good",
                                              field_id, fieldday_id)
                                # all slots filled w. games, no False state
                                continue
                            else:
                                # amount of status indices we are shifting is the beginning of the current 'true' segment until the
                                # end of the list
                                dst_begin = false_ind
                                src_begin = false_ind + true_ind
                                shift_length = fieldstatus_len - src_begin
                                logging.debug("ftscheduler:compaction:blockshift for field=%d gameday=%d from ind=%d to %d",
                                              field_id, fieldday_id, src_begin, dst_begin)
                                self.shiftGameDaySlots(fieldstatus_round, isgame_list, field_id, fieldday_id,
                                                       src_begin=src_begin, dst_begin=dst_begin, shift_len=shift_length)
                                for i in range(dst_begin+shift_length, fieldstatus_len):
                                    fieldstatus_round[i]['isgame'] = False
                finally:
                    fieldday_id += 1

    def getFieldSeasonStatus_list(self):
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldstatus_list = []
        for f in self.fieldinfo_list:
            f_id = f['field_id']
            divinfo_list = [self.divinfo_list[self.divinfo_indexerGet(p)]
                for p in f['primaryuse_list']]
            #  if the field has multiple primary divisions, take max of gameinterval and gamesperseason
            max_interval = max(x['gameinterval'] for x in divinfo_list)
            gameinterval = timedelta(0,0,0,0,max_interval)  # convert to datetime compatible obj
            # get max of totalgamedays defined in divinfo config
            totalgamedays_list = [x['totalgamedays'] for x in divinfo_list]
            # TODO: figure out strategy when totalgamedays are different between
            # divisions
            totalgamedays = max(totalgamedays_list)
            # number of days field is open every week
            totalfielddays = f['totalfielddays']
            # get calendarmap_list for field
            calendarmap_list = f['calendarmap_list']
            calendarmap_indexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(calendarmap_list)).get(x)
            # note the below is a duplicate check to one of the tests in
            # fieldcheckavailability
            # If checks do not produce consistent results look at test logic.
            if totalfielddays < totalgamedays:
                raise FieldTimeAvailabilityError("Note enough total fielddays %d to cover required totalgamedays" % (totalfielddays,),
                    totalgamedays_list)
                return None
            # leave gamestart and end_time as datetime objects as time objects do
            # not support addition/subtraction with timedelta objects
            game_start_dt = parser.parse(f['start_time'])
            end_dt = parser.parse(f['end_time'])
            # slotstatus_list has a list of statuses, one for each gameslot
            sstatus_list = []
            while game_start_dt + gameinterval <= end_dt:
                # for above, correct statement should be adding pure gametime only
                sstatus_list.append({'start_time':game_start_dt, 'isgame':False})
                game_start_dt += gameinterval
            sstatus_len = len(sstatus_list)
            # add round_id, assumes i is 0-indexed, and round_id is 1-indexed
            # when assigning fieldslots, round_id from the match generator should
            # match up with the round_id
            '''
            slotstatus_list = [{'fieldday_id':i,
                'game_date':calendarmap_list[calendarmap_indexerGet(i)]['date'],
                'sstatus_list':deepcopy(sstatus_list)}
                for i in range(1,totalfielddays+1)]
            '''
            slotstatus_list = []
            for fieldday_id in range(1, totalfielddays+1):
                calendarmap = calendarmap_list[calendarmap_indexerGet(fieldday_id)]
                game_date = calendarmap['date']
                slotstatus_dict = {'fieldday_id':fieldday_id, 'game_date':game_date}
                if 'start_time' in calendarmap:
                    # start_time in calendarmap indicates we have a specific start/
                    # endtime for that date (and field)
                    start_time = parser.parse(calendarmap['start_time'])
                    end_time = parser.parse(calendarmap['end_time'])
                    lstatus_list = []
                    while start_time + gameinterval <= end_time:
                        lstatus_list.append({'start_time':start_time,
                            'isgame':False})
                        start_time += gameinterval
                    slotstatus_dict['sstatus_list'] = lstatus_list
                else:
                    slotstatus_dict['sstatus_list'] = deepcopy(sstatus_list)
                slotstatus_list.append(slotstatus_dict)
            # ref http://stackoverflow.com/questions/4260280/python-if-else-in-list-comprehension for use of if-else in list comprehension
            fieldstatus_list.append({'field_id':f['field_id'],
                'slotstatus_list':slotstatus_list,
                'daygameslots_num':sstatus_len})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldstatus_list)).get(x)
        List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
        return List_Indexer(fieldstatus_list, fstatus_indexerGet)

    def checkFieldAvailability(self, totalmatch_tuple):
        '''check if there is enough field availability by comparing against what is
        required as dictated by divinfo configuration and also generated matches.
        Following comparisons are made:
        a)for each div, Compare # games per week versus # days fields available per week
        b)For each div, Compare total required games for each team and total open
        days for each field attached to div.  At least one field should be able
        cover the required game days (this is a simplification as minimum necessary
        requirement for all fields to contribute towards meeting the totalgamedays
        requirement)
        c)Make sure there are enough time slots across all fields attached to
        aggregated divs that make up the connected_div_list to cover time slots
        required by the matches generated for the connected divs '''
        totalmatch_list = totalmatch_tuple.dict_list
        totalmatch_indexerGet = totalmatch_tuple.indexerGet
        # http://stackoverflow.com/questions/653509/breaking-out-of-nested-loops
        for connected_div in self.connected_div_components:
            required_slots = 0
            field_id_set = set()
            for div_id in connected_div:
                divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
                field_id_list = divinfo['divfield_list']
                field_id_set.update(field_id_list)
                # get number of gamedays per week required by div
                div_numgdaysperweek = divinfo['numgdaysperweek']
                div_totalgamedays = divinfo['totalgamedays']
                totalmatch = totalmatch_list[totalmatch_indexerGet(div_id)]
                # for comparison criteria c) compute total number of required slots
                required_slots += totalmatch['gameslots_perround_num']*max(totalmatch['numgames_list'])
                # find # days per week available from fields attached to div
                dayweek_set = set()
                totalfielddays_list = []
                for field_id in field_id_list:
                    fieldinfo = self.fieldinfo_list[self.fieldinfo_indexerGet(field_id)]
                    dayweek_set.update(fieldinfo['dayweek_list'])
                    totalfielddays_list.append(fieldinfo['totalfielddays'])
                dayweek_set_len = len(dayweek_set)
                # check if there are enough gamedays during the week
                if dayweek_set_len < div_numgdaysperweek:
                    logging.error("Not enough gamedays in week for %d" % (div_id,))
                    raise FieldTimeAvailabilityError("!!!!!!!!!!!!!!!! Not enough gamedays in week, need %d days, but only %d available" % (div_numgdaysperweek, dayweek_set_len),
                        div_id)
                    break
                # check if there are enough totalfielddays to cover the total
                # gamedays required for each division
                if all_isless(totalfielddays_list, div_totalgamedays):
                    logging.error("Not enough field days to cover %d" % (div_id,))
                    raise FieldTimeAvailabilityError("!!!Not enough fielddays, need %d days, but only %d available" % (div_totalgamedays, max(totalfielddays_list)),
                        div_id)
                    break
                fieldcounter_list = [];
                if self.tminfo_list and self.tminfo_indexerMatch(div_id):
                    div_totalteams = divinfo['totalteams']
                    for tm_id in range(1, div_totalteams+1):
                        tminfo = self.tminfo_list[self.tminfo_indexerGet(
                            (div_id, tm_id))]
                        af_list = tminfo['af_list']
                        if af_list:
                            c_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldcounter_list)).get(x)
                            diluted_weight = 1.0/len(af_list)
                            # if a team has multiple preferred fields, then it's
                            # 'insistence' on a specific field is less than if it
                            # was requesting an affinity with a single field; thus
                            # the effective weight of how much it wants to use that
                            # field is factored by a weight which is the inverse of
                            # the number of fields it is asking affinity to
                            # NOTE the use of this weighted fieldcounter_list is TBD
                            for f in af_list:
                                c_index = c_indexerGet(f)
                                if c_index:
                                    fieldcounter_list[c_index]['eff_count'] += diluted_weight
                                else:
                                    fieldcounter_list.append({'field_id':f,
                                        'eff_count':diluted_weight})
            else:
                # assuming previous tests passed, check if there are enough field
                # slots to accomodate number of games
                available_slots = sum(self.fieldstatus_list[self.fstatus_indexerGet(x)]['daygameslots_num']*self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['totalfielddays'] for x in field_id_set)
                if available_slots < required_slots:
                    logging.error("Not enough total field slots to cover %d" % (div_id,))
                    raise FieldTimeAvailabilityError("!!!Not enough fielddays, need %d days, but only %d available" % (required_slots,available_slots), div_id)
                    break
                else:
                    # do the next check: affinity fields.  See if affinity field
                    # requests are too concentrated on a specific fields or set
                    # of fields
                    # implementation TBD, leave pass in for now
                    pass
                continue
            break
        else:
            # all loops completed, everything is ok
            return True
        # there was a break, check failed
        return False

    def find_commondates(self, field_list):
        ''' Find common dates from multiple calendarmap_lists and return the
        common dates, along with the fieldday_id's corresponding to each
        list '''
        # first create list of tuples, with x[0] field_id, x[1] calendarmap_list
        maptuple_list = []
        for f in field_list:
            calendarmap_list = self.fieldinfo_list[self.fieldinfo_indexerGet(f)]['calendarmap_list']
            calendarmap_indexerGet = lambda x: dict((p['date'],i) for i,p in enumerate(calendarmap_list)).get(x)
            maptuple_list.append((f, calendarmap_list, calendarmap_indexerGet))
        # use set comprehension as described in
        # https://docs.python.org/2/tutorial/datastructures.html#sets
        # to create list of sets of dates
        dateset_list = [{y['date'] for y in x[1]} for x in maptuple_list]
        # do an intersection amongst the sets to get common dates
        intersection_list = list(set.intersection(*dateset_list))
        # create the data structure to return the common dates
        commonmap_list = []
        for date in intersection_list:
            map_dict = {}
            for maptuple in maptuple_list:
                field_id = maptuple[0]
                calendarmap_list = maptuple[1]
                calendarmap_indexerGet = maptuple[2]
                fieldday_id = calendarmap_list[calendarmap_indexerGet(date)]['fieldday_id']
                # mapping dictionary maps field_id to fieldday_id
                map_dict.update({field_id:fieldday_id})
            commonmap_list.append({'date':date, 'map_dict':map_dict})
        commonmap_list.sort(key=itemgetter('date'))
        return commonmap_list

