''' Copyright YukonTR 2014 '''
from datetime import  datetime, timedelta
from itertools import groupby
from schedule_util import all_value, enum, shift_list, \
    bipartiteMatch, getConnectedDivisionGroup, all_isless, find_ge, find_le
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
import logging
from operator import itemgetter
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, \
     CodeLogicError, SchedulerConfigurationError
from math import ceil, floor
from collections import namedtuple, deque
import networkx as nx
from random import shuffle
from networkx import nx
from networkx.algorithms import bipartite
home_CONST = 'HOME'
away_CONST = 'AWAY'
firstslot_CONST = 0
verynegative_CONST = -1e6
verypositive_CONST = 1e6
balanceweight_CONST = 2
time_iteration_max_CONST = 18
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class TimeBalancer:
    def __init__(self, fstatus_tuple):
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        self._current_earlylate_list = list()
        self._target_earlylate_list = list()
        self._cel_indexerGet = None
        self._tel_indexerGet = None
        self._cel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self._current_earlylate_list)).get(x)
        self._tel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self._target_earlylate_list)).get(x)
        self._EL_enum = enum(NORMAL=0x0, EARLY_DIVTOTAL_NOTMET=0x1,
            LATE_DIVTOTAL_NOTMET=0x2, EARLY_TEAM_NOTMET=0x4, LATE_TEAM_NOTMET=0x8)
    ''' ref https://docs.python.org/2/library/functions.html#property
    on object getters/setters '''
    @property
    def current_earlylate_list(self):
        return self._current_earlylate_list
    @property
    def target_earlylate_list(self):
        return self._target_earlylate_list
    @property
    def cel_indexerGet(self):
        return self._cel_indexerGet
    @property
    def tel_indexerGet(self):
        return self._tel_indexerGet
    @property
    def EL_enum(self):
        return self._EL_enum

    def get_divtarget_el(self, divinfo_tuple, fieldinfo_list, div_id,
        div_totalgamedays):
        ''' get early/late target counts for the division.
        NOTE: review computation for divtarget_el for cases where there are
        multiple gameday availabilities for each round_id for example, if the
        matches spill over into the second (or later) or later gamedays within
        the same round_id, should there be credit towards satisfying early/late
        target counters?
        expected total fair share of number of early OR late games for each division
        eff_edgeweight represents 'fair share' of fields
        factor of 2 comes in because each time slots gets credited to two teams
        (home and away)'''
        ew_tuple = self.getDivFieldEdgeWeight_list(divinfo_tuple,
            fieldinfo_list)
        ew_list = ew_tuple.dict_list
        ew_indexerGet = ew_tuple.indexerGet
        divtarget_el = 2*div_totalgamedays*ew_list[ew_indexerGet(div_id)]['prodratio']
        return divtarget_el

    ''' create bipartite graph - one column is division, other column is fields
    used to define relationship between division and fields
    ref http://networkx.github.io/documentation/latest/reference/algorithms.bipartite.html'''
    def getDivFieldEdgeWeight_list(self, divinfo_tuple, fieldinfo_list):
        divinfo_list = divinfo_tuple.dict_list
        divinfo_indexerGet = divinfo_tuple.indexerGet
        df_biparG = nx.Graph()
        df_biparG.add_nodes_from([x['div_id'] for x in divinfo_list], bipartite=0)
        # even through we are using a bipartite graph structure, node names between
        # the column nodes need to be distinct, or else edge (1,2) and (2,1) are not distinguished.
        # instead use edge (1, f2), (2, f1) - use 'f' prefix for field nodes
        df_biparG.add_edges_from([(x['div_id'],'f'+str(y)) for x in divinfo_list for y in x['divfield_list']])
        div_nodes, field_nodes = bipartite.sets(df_biparG)
        deg_fnodes = {f:df_biparG.degree(f) for f in field_nodes}
        # effective edge sum lists for each division, the sum of the weights of the connected fields;
        # the weights of the associated fields, which are represented as field nodes,
        # are in turn determined by it's degree.  The inverse of the degree for the connected division is
        # taken, which becomes the weight of the particular field associated with the division.  The weights
        # of each field are summed for each division.  The weights also represent the 'total fairness share'
        # of fields associated with a division.
        # Bipartite graph representations, with divisions as one set of nodes, and fields as the other set
        # are used.  Thus a neighbor of a division is always a field.
        edgesum_list = [{'div_id':d,
            'edgesum': sum([1.0/deg_fnodes[f] for f in df_biparG.neighbors(d)])} for d in div_nodes]
        sorted_edgesum_list = sorted(edgesum_list, key=itemgetter('div_id'))
        logging.debug("div fields bipartite graph %s %s effective edge sum for each node %s", df_biparG.nodes(), df_biparG.edges(), sorted_edgesum_list)

        # depending on the number of teams in each division, the 'fairness share' for each division is adjusted;
        # i.e. a division with more teams is expected to contribute a larger amount to field sharing obligations,
        # such as the number of expected early/late start times for a particular division.  (If one div has 20 teams
        # and the other connected div has only 10 teams, the 20-team division should have a larger share of filling
        # early and late start time games.
        # ratio is represented as factor that is multiplied against the 'expected' fair share, which is the 1-inverse
        # of the number of divisions in the connected group - (dividing by the 1-inverse is equiv to multiple by the
        # number of teams - len(connected_list) as shown below)
        divratio_list = [{'div_id':x,
            'ratio': len(connected_list)*float(divinfo_list[divinfo_indexerGet(x)]['totalteams'])/sum(divinfo_list[divinfo_indexerGet(y)]['totalteams'] for y in connected_list)} for connected_list in getConnectedDivisionGroup(fieldinfo_list) for x in connected_list]
        sorted_divratio_list = sorted(divratio_list, key=itemgetter('div_id'))
        # multiply sorted edgesum list elements w. sorted divratio list elements
        # because of the sort all dictionary elements in the list should be sorted according to div_id and obviating
        # need to create an indexerGet function
        # x['div_id'] could have been y['div_id'] in the list comprehension below
        prod_list = [{'div_id': x['div_id'], 'prodratio': x['edgesum']*y['ratio']}
                                 for (x,y) in zip(sorted_edgesum_list, sorted_divratio_list)]
        logging.debug("getDivFieldEdgeWeight: sorted_edge=%s, sorted_ratio=%s, prod=%s",
                                    sorted_edgesum_list, sorted_divratio_list, prod_list)
        # define indexer function object
        prod_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(prod_list)).get(x)
        return _List_Indexer(prod_list, prod_indexerGet)

    ''' function to increment timeslot counters'''
    def incrementEL_counters(self, homecounter_dict, awaycounter_dict, el_str):
        homecounter_dict[el_str] += 1
        awaycounter_dict[el_str] += 1
        logging.debug("timebalancer:incrementELcounter: %s h=%s a=%s",
                      el_str, homecounter_dict, awaycounter_dict)

    ''' function to decrement timeslot counters'''
    def decrementEL_counters(self, homecounter_dict, awaycounter_dict, el_str):
        homecounter_dict[el_str] -= 1
        awaycounter_dict[el_str] -= 1
        logging.debug("timebalancer:decrementELcounter: %s h=%s a=%s",
            el_str, homecounter_dict, awaycounter_dict)
        return True

    def findTeamsDecrementEL_counters(self, field_id, slot_index, el_str, fieldday_id):
        ''' find teams from fieldSeasonStatus list and decrement early/late counters'''
        fieldstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(field_id)]
        slotstatus_list = fieldstatus_list['slotstatus_list']
        rg_index = fieldday_id-1
        slotteams = slotstatus_list[rg_index]['sstatus_list'][slot_index]['teams']
        slot_div = slotteams['div_id']
        slot_home = slotteams[home_CONST]
        slot_away = slotteams[away_CONST]
        cindex = self._cel_indexerGet(slot_div)
        slot_el_list = self._current_earlylate_list[cindex]['counter_list']
        home_slot_dict = slot_el_list[slot_home-1]
        away_slot_dict = slot_el_list[slot_away-1]
        self.decrementEL_counters(home_slot_dict, away_slot_dict, el_str)
        return True

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
                                    logging.debug("timebalancer:FindSwapMatchForTB: found slot0 field=%d div=%d fieldday=%d team=%d opp=%d",
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
                        logging.debug("timebalancer:findswapmatchtb: swap for div=%d team=%d is=%s",
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
                logging.debug("timebalancer:findswapmatchtb: swap=%s", swap)
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
        tel_index = self._tel_indexerGet(div_id)
        target_el_list = self._target_earlylate_list[tel_index]['target_list']
        cel_index = self._cel_indexerGet(div_id)
        current_el_list = self._current_earlylate_list[cel_index]['counter_list']
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
            logging.debug("timebalancer:retimebalance: swap info after bipartite match=%s", obj[0])
            swapteams_dict = obj[0]
            for key_slot in swapteams_dict:
                val_slot = swapteams_dict[key_slot]
                kteams = ftstatus[key_slot]['teams']
                vteams = ftstatus[val_slot]['teams']
                logging.debug("timebalancer:retimebalance: swapping teams %s at slot %d with teams %s at slot %d",
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
        logging.debug("timebalancer:retimebalance: type %s = sorted %s", el_type, sorted_list)
        # ref http://stackoverflow.com/questions/5695208/group-list-by-values for grouping by values
        diff_groups = [{eldiff_str: key, 'teams':[x['team_id'] for x in items]}
                       for key, items in groupby(sorted_list, itemgetter(eldiff_str))]
        logging.debug("timebalancer:retimebalance: group %s counters %s", el_type, diff_groups)
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
                logging.debug("timebalancer:retimebalance: div=%s %s time swap exceeds max", div_set, el_type)
                completeflag = False
                break
        else:
            completeflag = True
            logging.debug("timebalancer:retimebalance: div=%s %s balance achieved", div_set, el_type)
        return completeflag

    def ReTimeBalance(self, fieldset, connected_div_list):
        ''' Rebalance time schedules for teams that have excessive number of early/late games '''
        flag_dict = {}
        for el_type in ['early', 'late']:
            flag_dict[el_type] = False
            for i in range(3):
                estatus = self.ReTimeBalanceELIteration(connected_div_list, fieldset, el_type)
                if estatus:
                    logging.debug("timbalancer:retimebalance: eltype=%s divset=%s time balance SUCCEEDED", el_type, connected_div_list)
                    flag_dict[el_type] = True
                    break
            else:
                logging.debug("timbalancer:retimebalance: eltype=%s divset=%s ITERATION MAXED", el_type, connected_div_list)
        if all(flag_dict.values()):
            return True
        else:
            return False

    def IncDecELCounters(self, teams, el_type, increment):
        ''' inc/dec early/late counters based on el type and inc/dec flag '''
        div_id = teams['div_id']
        home_id = teams[home_CONST]
        away_id = teams[away_CONST]
        cel_index = self._cel_indexerGet(div_id)
        current_el_list = self._current_earlylate_list[cel_index]['counter_list']
        home_currentel_dict = current_el_list[home_id-1]
        away_currentel_dict = current_el_list[away_id-1]
        if increment:
            self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)
        else:
            self.decrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)
        return True

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
        return True


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
            logging.error("timebalancer:shiftFSstatus: field=%d status shows slot=%d has no game",
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
        cel_index = self._cel_indexerGet(div_id)
        cel_list = self._current_earlylate_list[cel_index]['counter_list']
        el_dict = cel_list[team_id-1]

        # also find out target early/late count values
        tel_index = self._tel_indexerGet(div_id)
        tel_list = self._target_earlylate_list[tel_index]['target_list']
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
        cel_index = self._cel_indexerGet(did)
        cel_list = self._current_earlylate_list[cel_index]['counter_list']
        home_el_dict = cel_list[home_ind]
        away_el_dict = cel_list[away_ind]

        # also find out target early/late count values
        tel_index = self._tel_indexerGet(did)
        tel_list = self._target_earlylate_list[tel_index]['target_list']
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

    def findconfirm_slot(self, field_id, fieldday_id, home_currentel_dict, away_currentel_dict, el_state, EL_enum):
        ''' Confirm if the candidate field_id and fieldday_id/date can be used
        to assign a game by checking fieldseason status list first for
        availability; if available, find optimal slot based on earliest
        availability, coupled with the requirement to meet early/late fairness
        distribution.
        Coding style note:  Instead of implementing an if..else if...else
        structure, code implemented with series of if .. return as there are
        cases when an inner if fails, other subsequent tests should be performed.
        '''
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
                raise CodeLogicError("timebalancer:findconfirm_slot: field_id inconsistency slotfield=%d field_id=%d" %
                    (slotfield_id, field_id))
            slot_index = fieldslotELtype_tuple.slot_index
            el_str = fieldslotELtype_tuple.el_str
            if slot_index == 0 and el_str == 'early':
                # shift the current scheduled games to the right one spot
                self.shiftFSstatus_list(field_id, slot_index,
                    fieldday_id)
            elif (slot_index == 0 and el_str != 'early') or (slot_index != 0 and el_str == 'early'):
                raise CodeLogicError("timebalancer:findBestSlot slot_index el_str logic error")
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

    def findBestSlot(self, match_list):
        ''' find best selection of field/slot index given by match_list parameter.
        Optimal choice is selected by finding max of 'measure' - initially defined
        to be the sum of the differences of home and away counts compared to target.
        This function is created so that even when EL_enum state is 'normal', and
        optimal choice can be made to insert at either the beginning or end of the
        gameday schedule.  Created to provided flexibility when total or per-team
        div early/late counts have met their targets '''
        rflag = False
        fs_list = []
        for field_match in match_list:
            field_id = field_match['field_id']
            # zip is used in for loop because we assume that early and late counters are relevant
            # to first and last matches (respectively) exclusively.
            # see calling function for how newslot paramenters are assigned.
            for (matchtype, el_str, slotind) in zip(['firstmatch', 'lastmatch'],
                ['early', 'late'], ['firstmatch_newslot', 'lastmatch_newslot']):
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

    def RecomputeCEL_list(self, fset, div_set):
        ''' recompute current_earlylist_counter structure by going through fieldseasonstatus matrix '''
        for div_id in div_set:
            # first clear counters
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            totalteams = divinfo['totalteams']
            for elcounter in self._current_earlylate_list[self._cel_indexerGet(div_id)]['counter_list']:
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
                    cel_index = self._cel_indexerGet(div_id)
                    current_el_list = self._current_earlylate_list[cel_index]['counter_list']
                    home_currentel_dict = current_el_list[home_id-1]
                    away_currentel_dict = current_el_list[away_id-1]
                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, el_type)
