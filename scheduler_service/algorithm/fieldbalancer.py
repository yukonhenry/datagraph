''' Copyright YukonTR 2013 '''
from datetime import  datetime
from util.schedule_util import all_value, enum, shift_list, \
    all_isless, find_le
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
import logging
from operator import itemgetter
from util.sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, \
     CodeLogicError, SchedulerConfigurationError
from math import ceil, floor
from collections import namedtuple

HOME = 'HOME'
AWAY = 'AWAY'
GAME_TEAM = 'game_team'
BALANCEWEIGHT = 2
field_iteration_max_CONST = 15
mindiff_count_max_CONST = 4
MAX_ABS_DIFFWEIGHT = 0.51
MAX_FIELDBALANCE_ITERATION_COUNT = 100
VERY_LARGE = 1e6
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class FieldBalancer(object):
    def __init__(self, divinfo_tuple, fstatus_tuple, tminfo_tuple, timebalancer):
        self.divinfo_list = divinfo_tuple.dict_list
        self.divinfo_indexerGet = divinfo_tuple.indexerGet
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        if tminfo_tuple:
            self._tminfo_list = tminfo_tuple.dict_list
            # for indexerGet, parameter is two-tuple (div_id, tm_id)
            # returns None or index into tminfo_list
            self._tminfo_indexerGet = tminfo_tuple.indexerGet
            # for indexerMatch
            self._tminfo_indexerMatch = tminfo_tuple.indexerMatch
        else:
            self._tminfo_list = None
            self._tminfo_indexerGet = None
            self._tminfo_indexerMatch = None
        self.timebalancer = timebalancer

    # define setter getter methods
    # Ensure class inherits from object
    # ref http://stackoverflow.com/questions/598077/why-does-foo-setter-in-python-not-work-for-me
    @property
    def tminfo_list(self):
        return self._tminfo_list

    @tminfo_list.setter
    def tminfo_list(self, value):
        self._tminfo_list = value

    @property
    def tminfo_indexerGet(self):
        return self._tminfo_indexerGet

    @tminfo_indexerGet.setter
    def tminfo_indexerGet(self, value):
        self._tminfo_indexerGet = value

    @property
    def tminfo_indexerMatch(self):
        return self._tminfo_indexerMatch

    @tminfo_indexerMatch.setter
    def tminfo_indexerMatch(self, value):
        self._tminfo_indexerMatch = value

    def findMinimumCountField(self, homemetrics_list,
        awaymetrics_list, rd_fieldcount_list, reqslots_perrnd_num,
        hf_list, field_list, targetfieldcount_list, divref_list, divteamref_list,
        submin=0):
        # This method returns an ordered list of candidate fields to the ftschedler,
        # which makes an initial field/date/time schedule assignment for the match.
        # The field list is ordered according to the cost function value for each
        # field, which is a sum of the field cost for both the home and away team
        # for the current match that is being scheduled.  Each field cost for the
        # home and way teams is calculated by a pentaly function for the field
        # that is applied acoording to how close it is or has alredy exceeded
        # the target counts.
        # ----
        # Also pass in the minmaxdate_list and field_list - we want to find fields
        # that satisfy
        # the minimum-date criteria - fill up fields on earlier calendar date
        # before starting to fill a later calendar date, even if violating field
        # count balancing requirements.  For example, if Field 1 is available on
        # Saturdays only and Field 2 is available on Sundays only - if teams
        # are only playing once during that weekend, have them play on Field1
        # on Saturdays until they have to play on Sunday/Field 2 because Sat/
        # Field1 is full, even though this will not meet field balancing
        # requirements.
        #--------------------------
        # get full home field lists(e.g. home field for 'away'-designated teams)
        # if there are no fields specified, then default to full list for that
        # team
        '''
        aggregnorm_list = aggregnorm_tuple.dict_list
        agindexerGet = aggregnorm_tuple.indexerGet
        targetfieldcount_list = [{'field_id':x,
            'count':int(round(aggregnorm_list[agindexerGet(x)]['normweight']*reqslots_perrnd_num))} for x in field_list]
        # verify individual count elements sum up to total number of slots required per round
        sumcount = sum(x['count'] for x in targetfieldcount_list)
        if sumcount != reqslots_perrnd_num:
            # if test fails, reassign last entry so that sum is consistent w
            # expected value
            partial_sum = sum(x['count'] for x in targetfieldcount_list[:-1])
            # overwrite last element
            targetfieldcount_list[-1]['count'] = reqslots_perrnd_num - partial_sum
        '''
        tindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(
            targetfieldcount_list)).get(x)
        if hf_list:
            home_af_list = hf_list[0]['af_list']
            away_af_list = hf_list[1]['af_list']
            home_hf_set = set(home_af_list) if home_af_list else set(field_list)
            away_hf_set = set(away_af_list) if away_af_list else set(field_list)
        else:
            home_hf_set = set(field_list)
            away_hf_set = set(field_list)
        # hfunion_list represents the union of designated (or default) home fields
        # e.g. the list of assignalbe fields
        hfunion_set = set.union(home_hf_set, away_hf_set)
        # filter input lists with hfunion_set as metrics measurements or
        # finding descent direction involving fields that are not relevant
        # for the round is meaningless (control var not part of domain set)
        #-----
        # field count list for current round
        eff_rd_fcount_list = [x for x in rd_fieldcount_list
            if x['field_id'] in hfunion_set]
        erd_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(eff_rd_fcount_list)).get(x)

        fielddiffcount_list = [{'field_id':x,
            'diffcount':targetfieldcount_list[tindexerGet(x)]['count']-eff_rd_fcount_list[erd_indexerGet(x)]['count']}
                for x in hfunion_set]
        ##**********************
        # convergence parameter calculation for per-field targets
        for fielddiffcount in fielddiffcount_list:
            diffcount = fielddiffcount['diffcount']
            if diffcount <= 0:
                penalty = abs(diffcount-1)*2
                # penalty makes the diffcount even more negative
                fielddiffcount['diffcount'] = (diffcount-1)*penalty
            elif diffcount > 0:
                # count is approaching reference, define penalty
                # additive penalty towards reaching/exceeding reference
                penalty = diffcount
                fielddiffcount['diffcount'] *= penalty
        findexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(
            fielddiffcount_list)).get(x)
        # field counter for home team
        eff_homemetrics_list = [x for x in homemetrics_list
            if x['field_id'] in hfunion_set]
        # field counter for away team
        eff_awaymetrics_list = [x for x in awaymetrics_list
            if x['field_id'] in hfunion_set]
        ehindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(eff_homemetrics_list)).get(x)
        eaindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(eff_awaymetrics_list)).get(x)
        if divteamref_list and hf_list:
            # per team field distribution info is available - compare run time
            # field counts for team against reference
            dtindexerGet = lambda x: dict((p['team_id'],i) for i,p in enumerate(divteamref_list)).get(x)
            home_id = hf_list[0]['team_id']
            away_id = hf_list[1]['team_id']
            home_sumweight_list = divteamref_list[dtindexerGet(home_id)]['sumweight_list']
            away_sumweight_list = divteamref_list[dtindexerGet(away_id)]['sumweight_list']
            hsindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(home_sumweight_list)).get(x)
            asindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(away_sumweight_list)).get(x)
            # diff is reference - current running count (think control)
            # large positive value indicates more control (game needs to be added)
            # required for that field
            home_diffcount_list = [{'field_id':x,
                'diffcount':home_sumweight_list[hsindexerGet(x)]['sumweight'] -eff_homemetrics_list[ehindexerGet(x)]['count']}
                for x in hfunion_set]
            hdindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(home_diffcount_list)).get(x)
            away_diffcount_list = [{'field_id':x,
                'diffcount':away_sumweight_list[asindexerGet(x)]['sumweight'] -eff_awaymetrics_list[eaindexerGet(x)]['count']}
                for x in hfunion_set]
            adindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(away_diffcount_list)).get(x)
            # *****************************
            # Review penalty weight constants here
            for diffcount_list in [home_diffcount_list, away_diffcount_list]:
                for diffcount_dict in diffcount_list:
                    diffcount = diffcount_dict['diffcount']
                    if diffcount <= 0:
                        # count has exceeded reference, define penalty
                        penalty = abs(diffcount-1)*2
                        # penalty makes the diffcount even more negative
                        diffcount_dict['diffcount'] = (diffcount-1)*penalty
                    elif diffcount == 1:
                        # count is approaching reference, define penalty
                        # additive penalty towards reaching/exceeding reference
                        penalty = 1
                        diffcount_dict['diffcount'] -= penalty
            # cost function is determined by summing home and away team field
            # distribution counts (counts taken into account penalty as calculated)
            # above
            # also take into account how fields in division are being filled -
            # sum field target differences to team target difference
            sumdiffcount_list = [{'field_id':x,
                'sumdiffcount':home_diffcount_list[hdindexerGet(x)]['diffcount'] + away_diffcount_list[adindexerGet(x)]['diffcount'] +
                    2*fielddiffcount_list[findexerGet(x)]['diffcount']} for x in hfunion_set]
            # get unique set of sumdiffcount values
            uniquecount_list = list(
                set([x['sumdiffcount'] for x in sumdiffcount_list]))
            sorted_sumdiffcount_list = [{'sumdiffcount':x,
                'field_list':[y['field_id'] for y in sumdiffcount_list if y['sumdiffcount']==x]} for x in uniquecount_list]
            sorted_sumdiffcount_list.sort(key=itemgetter('sumdiffcount'),
                reverse=True)
            return sorted_sumdiffcount_list
        else:
            # note there seems to be a weird pdb problem here - pdb does not break
            # if a pass statement is placed here and a breakpoint added; if the
            # pass statement is replaced with any other statement like a simple
            # print statement, pdb breaks as expected when control flow passes
            # through
            raise CodeLogicError("fbalancer:findMinimumCount: divteamref_list or hf_list is None")
        # Calc first order target max number of games per field per round
        # assuming each field should carry equal share (old note for equal field
        # balancing)
        # note we are using the number of all fields instead of the number
        # of fields from the filtered list as the required (or the target)
        # slot number should be based on all fields available for entire div.
        # get aggregate home field weight list
        norm_hfweight_list = aggregnorm_tuple.dict_list
        # get sum of weights so that we can compute norm
        #sumweight = sum(x['aggregweight'] for x in ag_hfweight_list)
        # normalize each of the weights
        #norm_hfweight_list = [{'field_id':x['field_id'],
        #    'normweight':x['aggregweight']/sumweight} for x in ag_hfweight_list]
        # compute the required slots for each field by multiplying the total
        # required slots per round times the normalized weighting factor
        reqslots_list = [{'field_id':x['field_id'], 'count':int(round(float(reqslots_perrnd_num)*x['normweight']))} for x in norm_hfweight_list]
        if sum(x['count'] for x in reqslots_list) != reqslots_perrnd_num:
            # if sum of per-field counts do not equal the total req slots for
            # connected div, force it
            rlen = len(reqslots_list)
            partialsum = sum(x['count'] for x in reqslots_list[:rlen])
            reqslots_list[rlen-1] = reqslots_perrnd_num - partialsum

        req_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(reqslots_list)).get(x)
        diff_count_list = [{'field_id':x,
            'diff_count':eff_rd_fcount_list[erd_indexerGet(x)]['count'] -
            reqslots_list[req_indexerGet(x)]['count']} for x in hfunion_set]
        maxdiff_dict = max(diff_count_list, key=itemgetter('diff_count'))
        #requiredslots_perfield = int(ceil(
        #    float(reqslots_perrnd_num)/len(rd_fieldcount_list)))
        maxedout_field = None
        almostmaxed_field = None
        maxdiff = maxdiff_dict['diff_count']
        # get count/field dict with maximum count
        # assign penalty costs for fields that have either already exceeded
        # or close to exceeing the maximum
        #maxgd = max(eff_rd_fcount_list, key=itemgetter('count'))
        #for gd in eff_rd_fcount_list:
        #diff = maxgd['count'] - requiredslots_perfield
        if maxdiff >= 0:
            #******** cost function
            # 1 is a slack term, arbitrary
            maxedout_field = maxdiff_dict['field_id']
            penalty = (maxdiff + 1)*2
        elif maxdiff >= -1:
            almostmaxed_field = maxdiff_dict['field_id']
            penalty = maxdiff + 2 # impose additive penalty
        # first ensure both lists are sorted according to field
        # note when calling the sorted function, the list is only shallow-copied.
        # changing a field in the dictionary element in the sorted list also
        # changes the dict in the original list
        # we should make a copy of the list first before sorting
        sorted_homemetrics_list = sorted(eff_homemetrics_list, key=itemgetter('field_id'))
        sorted_awaymetrics_list = sorted(eff_awaymetrics_list, key=itemgetter('field_id'))
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
            # since homecount_list and awaycount_list are made from the respective
            # sorted (according to field) metrics list, maxedout_ind should
            # correspond to the maxed field for both homecount and awaycount lists
            homecount_list[maxedout_ind] = (homecount_list[maxedout_ind]+1)*penalty
            awaycount_list[maxedout_ind] = (awaycount_list[maxedout_ind]+1)*penalty
            logging.info("fbalancer:findMinCountField: field=%d maxed out, required=%s ind=%d penalty=%d",
                maxedout_field, maxdiff_dict, maxedout_ind, penalty)
            logging.info("fbalancer:findMinCountField: weighted lists home=%s away=%s",
                homecount_list, awaycount_list)
        elif almostmaxed_field:
            # if the current field count is almost (one less than) the target count, then incrementally
            # the home/away count list for the field as a penalty - this will incrementally 'slow down'
            # target count from being reached
            almost_ind = home_field_list.index(almostmaxed_field)
            # if count is approaching the limit, give an additive penalty
            homecount_list[almost_ind] += penalty
            awaycount_list[almost_ind] += penalty
            logging.info("fbalancer:findMinCountField: field=%d Almost Target, required=%s ind=%d",
                almostmaxed_field, maxdiff_dict, almost_ind)
            logging.info("fbalancer:findMinCountField: weighted lists home=%s away=%s",
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

    def getFieldTeamCount(self, tfmetrics, field_id, team_id):
        ''' get field count for team specified - extracted from tfmetrics (teamfieldmetrics extracted by
        div_id from fieldmetrics_list '''
        metrics_list = tfmetrics[team_id-1]
        metrics_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(metrics_list)).get(x)
        count = metrics_list[metrics_indexerGet(field_id)]['count']
        return count

    def get_teamfield_diffweight(self, divteam_diffweight_list, dtindexerGet,
        team_id, field_list):
        ''' get diffweights for designated team and field id '''
        team_diffweight_list = divteam_diffweight_list[dtindexerGet(team_id)]['diffweight_list']
        findexerGet = lambda x: dict((p['field_id'],i)
            for i,p in enumerate(team_diffweight_list)).get(x)
        return [team_diffweight_list[findexerGet(f)]['diffweight']
            for f in field_list]

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

    def CompareDivFieldDistribution(self, connected_div_list, fieldmetrics_list,
        findexerGet, divref_tuple):
        ''' Compare division level field distribution to reference (expected)
        distribution '''
        divref_list = divref_tuple.dict_list
        dindexerGet = divref_tuple.indexerGet
        actualref_diff_list = list()
        for div_id in connected_div_list:
            # get reference division-wide field count
            ref_distrib_list = divref_list[dindexerGet(div_id)]['distrib_list']
            rindexerGet = lambda x: dict((p['field_id'],i)
                for i,p in enumerate(ref_distrib_list)).get(x)
            field_list = [x['field_id'] for x in ref_distrib_list]
            # get measured
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            # sum up per-team field use to get division-wide field use metrics
            actual_distrib_list = [{'field_id':field_id,
                'sumcount': sum(x['count'] for y in tfmetrics for x in y
                    if x['field_id']==field_id)} for field_id in field_list]
            aindexerGet = lambda x: dict((p['field_id'],i)
                for i,p in enumerate(actual_distrib_list)).get(x)
            # for each field get difference: reference - actual
            diff_distrib_list = [{'field_id':f,
                'diffcount':actual_distrib_list[aindexerGet(f)]['sumcount'] -
                    ref_distrib_list[rindexerGet(f)]['sumcount']
                } for f in field_list]
            actualref_diff_list.append({'div_id':div_id,
                'distrib_list':diff_distrib_list})
        aindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(actualref_diff_list)).get(x)
        return _List_Indexer(actualref_diff_list, aindexerGet)

    def identify_control_div(self, teamdiff_tuple):
        ''' return divisions that have any abs teamdiffcount greater than 0.49
        example teamdiff_list structure [
            {'div_id': 1, 'div_diffweight_list': [
                {'team_id': 1, 'diffweight_list':
                    [{'diffweight': 0.0, 'field_id': 1},
                    {'diffweight': 0.0, 'field_id': 2}]
                },
                {'team_id':2, 'diffweight_list':[]}
            },
            {'div_id':2, 'div_diffweight_list':[]}, ....
        ]
        '''
        teamdiff_list = teamdiff_tuple.dict_list
        convergence_list = [{'div_id':x['div_id'],
            'convergence_count':sum(abs(z['diffweight']) > MAX_ABS_DIFFWEIGHT for y in x['div_diffweight_list'] for z in y['diffweight_list'])} for x in teamdiff_list]
        '''
        non-list comprehension implementation
        control_div_set = set()
        for divteamdiff_dict in teamdiff_list:
            div_id = divteamdiff_dict['div_id']
            for divteamdiff in divteamdiff_dict['div_diffweight_list']:
                if any(abs(x['diffweight']) > 0.49 for x in divteamdiff['diffweight_list']):
                    control_div_set.update(div_id)
                    break
        '''
        # alternate list comprehension - don't know which is more efficient as
        # the above has a break statement that prevents all teams from being searched
        control_div_list = [x['div_id'] for x in teamdiff_list
            if any(abs(z['diffweight']) > MAX_ABS_DIFFWEIGHT for y in x['div_diffweight_list'] for z in y['diffweight_list'])]
        dual_list_tuple = namedtuple('dual_list_tuple',
            'convergence_list control_div_list')
        return dual_list_tuple(convergence_list, control_div_list)

    def apply_teamdiff_control(self, teamdiff_tuple, cdiv_list,
        fieldmetrics_list, findexerGet, commondates_list):
        teamdiff_list = teamdiff_tuple.dict_list
        tindexerGet = teamdiff_tuple.indexerGet
        # create set in case there are div_id duplicates
        div_set = set(cdiv_list)
        for div_id in div_set:
            # get list of team diff weights for specified division
            divteam_diffweight_list = teamdiff_list[tindexerGet(div_id)]['div_diffweight_list']
            dtindexerGet = lambda x: dict((p['team_id'],i)
                for i,p in enumerate(divteam_diffweight_list)).get(x)
            # get current field count metrics for specified div_id
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            for team_diffweight in divteam_diffweight_list:
                # iterate through each team_id and it's diff weight list
                # get reference team id and it's diffweights for each field
                team_id = team_diffweight['team_id']
                diffweight_list = team_diffweight['diffweight_list']
                dfindexerGet = lambda x: dict((p['field_id'],i)
                    for i,p in enumerate(diffweight_list)).get(x)
                # sort diffweights from lowest to highest
                # large neg value indicates field is oversubscribed (ref-actual)
                diffweight_list.sort(key=itemgetter("diffweight"))
                # get smallest weight value
                over_dict = diffweight_list[0]
                over_diffweight = over_dict['diffweight']
                if over_diffweight > MAX_ABS_DIFFWEIGHT:
                    # if smallest weight exceedes -max value, we will have swap
                    # candidates
                    #over_field_list = [x['field_id'] for x in diffweight_list
                    #    if x['diffweight'] < -MAX_ABS_DIFFWEIGHT]
                    # first keep it simple where we identify the most over-
                    # subscribed and under-subscribed fields and try to swap
                    # between them (instead of trying to see if we can swap
                    # amongst secondary subscribed fields)
                    over_field_id = over_dict['field_id']
                    over_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(over_field_id)]['slotstatus_list']
                    ovindexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(over_ftstatus_list)).get(x)
                    # swap in candidate below (undersusbscribed)
                    under_dict = diffweight_list[len(diffweight_list)-1]
                    under_field_id = under_dict['field_id']
                    under_diffweight = under_dict['diffweight']
                    # benefit to swap out reference team from oversubscribed field
                    # to undersubscribed field =
                    # -(oversubscribed cost - undersubscribed cost)
                    # = undersubscribed cost - oversubscribed cost
                    # the minus sign outside of the parentheses is to make the cost
                    # positive as typically oversubscribed will be a neg value and
                    # undersubscribed a positive value; also we will be taking a
                    # max of the total cost so we want teamswap_benefit_cost to be
                    # positive
                    teamswap_benefit_cost = over_diffweight - under_diffweight
                    # get max and min slot status lists and corresponding indexerget
                    # functions
                    under_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(under_field_id)]['slotstatus_list']
                    unindexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(under_ftstatus_list)).get(x)
                    fieldday_totalcost_list = list()
                    for cdates_dict in commondates_list:
                        # get fieldday_id that corresponds to field_id for current
                        # common date; commondates_dict[map_dict] key:value is
                        # field_id:fielday_id
                        over_fieldday_id = cdates_dict['map_dict'][over_field_id]
                        under_fieldday_id = cdates_dict['map_dict'][under_field_id]
                        #get fieldstatus list for the over and under fieldday_id
                        over_ftstatus = over_ftstatus_list[ovindexerGet(over_fieldday_id)]
                        under_ftstatus = under_ftstatus_list[unindexerGet(under_fieldday_id)]
                        # see if the re team is playing on the over field on
                        # the current game date.  If so, get game data.
                        over_fieldmatch_list = [{'slot_index':i,
                            'teams':j['teams']}
                            for i,j in enumerate(over_ftstatus['sstatus_list'])
                            if j['isgame'] and j['teams']['div_id']==div_id and
                            (j['teams'][HOME]==team_id or
                                j['teams'][AWAY]==team_id)]
                        if not over_fieldmatch_list:
                            continue # go to the next common date
                        elif len(over_fieldmatch_list) > 1:
                            logging.info("fbalancer:applytdiffcontrol:over field match list has more than on match for div %d, team %d on date %s" % (div_id, team_id, cdates_dict['date']))
                        # NOTE: assume only one game per day for now
                        over_fieldmatch = over_fieldmatch_list[0]
                        over_teams = over_fieldmatch['teams']
                        over_slot_index = over_fieldmatch['slot_index']
                        # get information necessary to determine early/late slot
                        # costs
                        over_isgame_list = [x['isgame'] for x in over_ftstatus['sstatus_list']]
                        over_lastTrue_slot = len(over_isgame_list)-1-over_isgame_list[::-1].index(True)
                        # even though we are not doing time balancing here, take
                        # into account time balance penalty into const function
                        # the higher the measure, the more we want to move it away
                        # from the over_field because el targets are exceeded
                        over_el_cost = self.timebalancer.getELcost_by_slot(
                            over_slot_index, over_teams, over_lastTrue_slot)
                        # get opponent team info and it's current counts for the
                        # over and undersubscribed fields
                        oppteam_id = over_teams[HOME] if over_teams[AWAY]==team_id else over_teams[AWAY]
                        # get the opponent team diffweights corresponding to the
                        # over and under subscribed fields
                        [opp_over_diffweight, opp_under_diffweight] = self.get_teamfield_diffweight(
                            divteam_diffweight_list, dtindexerGet, oppteam_id,
                            [over_field_id, under_field_id])
                        # seen notes above teamswap_benefit_cost on why benefit
                        # cost is under-over (instead of over-under) (we want
                        # cost to be positive)
                        opp_teamswap_benefit_cost = opp_over_diffweight - \
                            opp_under_diffweight
                        # We are ready for calculating the cost (measure of
                        # desirability) to swap out the match game from the
                        # oversubscribed field
                        # The cost will consiste: early/late measure (non-zero
                        # only is slot is 0 or last slot; positive only if at least
                        # one of the teams have already exceeded target);
                        # ref team benefit cost; opponent team benefit cost;
                        # a scaling factore is applied to the latter two as field
                        # cost crieteria is weighted more than early/late penalty
                        # costs
                        over_swapout_cost = over_el_cost + \
                            BALANCEWEIGHT*opp_teamswap_benefit_cost
                        over_swapout_metrics = {
                            'team':team_id, 'oppteam_id':oppteam_id,
                            'fieldday_id':over_fieldday_id,
                            'swapout_cost':over_swapout_cost
                        }
                        # Now we are going to search through the undersubscribed
                        # field to find a match to swap;
                        # Search in other div's also, but only if they are part
                        # of the control div list (don't distrib fully balanced
                        # divs)
                        under_fieldmatch_list = [{'slot_index':i,
                            'teams':j['teams']}
                            for i,j in enumerate(under_ftstatus['sstatus_list'])
                            if j['isgame'] and j['teams']['div_id'] in div_set]
                        if not under_fieldmatch_list:
                            continue # go to the next common date
                        under_isgame_list = [x['isgame'] for x in under_ftstatus['sstatus_list']]
                        under_lastTrue_slot = len(under_isgame_list)-1-under_isgame_list[::-1].index(True)
                        for under_fieldmatch in under_fieldmatch_list:
                            under_teams = under_fieldmatch['teams']
                            uhome_id = under_teams[HOME]
                            uaway_id = under_teams[AWAY]
                            under_slot_index = under_fieldmatch['slot_index']
                            # get cost (desirability to swap out) because of el_cost
                            # for underfield match
                            under_el_cost = self.timebalancer.getELcost_by_slot(
                                under_slot_index, under_teams, under_lastTrue_slot)
                            # get el_cost for moving the under field match team to
                            # the slot of the over field match.  Note get cost value
                            # assuming that the swap has already been made -
                            # appropriate subtractive term will be added for total
                            # cost calculation, as the higher the value, the less
                            # desirable to make the swap
                            # Note slot index and lastTrue slot are for over field
                            # match
                            under_to_over_el_cost = self.timebalancer.getELcost_by_slot(over_slot_index, under_teams,
                                over_lastTrue_slot)
                            # also get el_cost for moving the over field match team
                            # to under field match slot
                            # the higher the el_cost, the less desirable to swap in
                            # (this term will be subtracted)
                            over_to_under_el_cost = self.timebalancer.getELcost_by_slot(under_slot_index, over_teams,
                                under_lastTrue_slot)
                            # get diffweight of home_id from match at underfield
                            # for both the underfield but also at overfield -
                            # both needed to calculate costs moving from under
                            # field to overfield
                            [underhome_overfield_diffweight,
                            underhome_underfield_diffweight] = \
                                self.get_teamfield_diffweight(
                                divteam_diffweight_list, dtindexerGet, uhome_id,
                                [over_field_id, under_field_id])
                            # home swap cost for under field match is
                            # (we will be taking max)
                            # rem diffweight is actual-ref so diff will be positive
                            # if the field is oversubscribed, and negative if under-
                            # subscribed - ideally we want to find teams that are
                            # oversubscrubed in the under field
                            under_homeswap_cost = underhome_underfield_diffweight -\
                                underhome_overfield_diffweight
                            # similar calculations for underfield match away team
                            [underaway_overfield_diffweight,
                            underaway_underfield_diffweight] = \
                                self.get_teamfield_diffweight(
                                divteam_diffweight_list, dtindexerGet, uaway_id,
                                [over_field_id, under_field_id])
                            under_awayswap_cost = underaway_underfield_diffweight -\
                                underaway_overfield_diffweight
                            under_swap_cost = under_homeswap_cost + under_awayswap_cost
                            # calculate totalswap cost for this under field match
                            # rem cost is desirability to swap - optimal match is
                            # based on maxmization of cost function
                            under_fieldmatch['totalswap_cost'] = \
                                BALANCEWEIGHT*under_swap_cost + under_el_cost - \
                                over_to_under_el_cost - under_to_over_el_cost
                        max_under_fieldmatch = max(under_fieldmatch_list,
                            key=itemgetter('totalswap_cost'))
                        fieldday_totalcost = {
                            'oppteam_id':oppteam_id,
                            'over_fieldday_id':over_fieldday_id,
                            'under_fieldday_id':under_fieldday_id,
                            'over_slot_index':over_slot_index,
                            'under_slot_index':max_under_fieldmatch['slot_index'],
                            'under_teams':max_under_fieldmatch['teams'],
                            'over_lastTrue_slot':over_lastTrue_slot,
                            'under_lastTrue_slot':under_lastTrue_slot,
                            'total_cost':max_under_fieldmatch['totalswap_cost'] +\
                                over_swapout_cost
                        }
                        logging.debug("fbalancer:applytdiffcontrol:fieldday totalcost=%s" % (fieldday_totalcost,))
                        fieldday_totalcost_list.append(fieldday_totalcost)
                    # find fieldday and match data that gives max totalcost
                    max_totalcost = max(fieldday_totalcost_list,
                        key=itemgetter('total_cost'))
                    # get fieldday_ids that give max totalcost (fieldday id will
                    # typcially be the same, but can be different because fieldday
                    # id sequence is unique to the field)
                    max_over_fieldday_id = max_totalcost['over_fieldday_id']
                    max_under_fieldday_id = max_totalcost['under_fieldday_id']
                    # get match slot indexes into respective fielddays
                    max_over_slot_index = max_totalcost['over_slot_index']
                    max_under_slot_index = max_totalcost['under_slot_index']
                    # get sstatus lists for over and under fields
                    max_over_sstatus_list = over_ftstatus_list[ovindexerGet(
                        max_over_fieldday_id)]['sstatus_list']
                    max_under_sstatus_list = under_ftstatus_list[unindexerGet(
                        max_under_fieldday_id)]['sstatus_list']
                    # get match info for over and under fields
                    max_over_teams = max_over_sstatus_list[max_over_slot_index]['teams']
                    max_under_teams = max_under_sstatus_list[max_under_slot_index]['teams']
                    # perform consistency check with max_over_teams - should map
                    # to reference team and its opponent
                    max_home = max_over_teams[HOME]
                    max_away = max_over_teams[AWAY]
                    max_oppteam = max_totalcost['oppteam_id']
                    if not (max_over_teams['div_id'] == div_id and
                        (max_home == team_id or max_away == team_id) and
                        (max_home == max_oppteam or max_away == max_oppteam)):
                        raise CodeLogicError("fbalancer:applytdiffcontrol:optimal max overutilized field match %s does not match with ref div %d team %d oppontent %d" % (max_over_teams,
                            div_id, team_id, max_oppteam))
                        return None
                    logging.debug("fbalancer:applytdiffcontrol: before swap max_over_teams=%s max_under_teams=%s div=%d ref team=%d oppteam=%d" %
                        (max_over_teams, max_under_teams, div_id, team_id,
                        max_totalcost['oppteam_id']))
                    # do match swap
                    max_over_sstatus_list[max_over_slot_index]['teams'] = \
                        max_under_teams
                    max_under_sstatus_list[max_under_slot_index]['teams'] = \
                        max_over_teams
                    # increment/decrement fieldmetrics
                    # max overf teams moves out of over field_id, so decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet,
                        over_field_id, max_over_teams, increment=False)
                    # max overf teams moves into under field_id, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet,
                        under_field_id, max_over_teams, increment=True)
                    # max underf teams moves out of under field_id, decrement
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet,
                        under_field_id, max_under_teams, increment=False)
                    # max underf teams moves into over field_id, increment
                    self.IncDecFieldMetrics(fieldmetrics_list, findexerGet,
                        over_field_id, max_under_teams, increment=True)
                    # next adjust EL counters for max overf and underf teams
                    self.timebalancer.updateSlotELCounters(max_over_slot_index,
                        max_under_slot_index, max_over_teams, max_under_teams,
                        lastTrue_slot1 = max_totalcost['over_lastTrue_slot'],
                        lastTrue_slot2 = max_totalcost['under_lastTrue_slot'])
                else:
                    # no swap candidates, got to next team id
                    continue
        return True

    def CompareTeamFieldDistribution(self, connected_div_list, fieldmetrics_list,
        findexerGet, teamref_tuple):
        ''' Get actual-reference (minus, subtraction) for field distribution
        counts at the per-team level '''
        teamref_list = teamref_tuple.dict_list
        tindexerGet = teamref_tuple.indexerGet
        connected_diffweight_list = list()
        for div_id in connected_div_list:
            # get team reference
            div_sumweight_list = teamref_list[tindexerGet(div_id)]['div_sw_list']
            if not div_sumweight_list:
                # if no team weight list for current division, skip comparison and
                # go to next div_id
                # actually this should never happen as sw_list should always exist
                # even when af_list is not configured
                continue
            dindexerGet = lambda x: dict((p['team_id'],i) for i,p in enumerate(div_sumweight_list)).get(x)
            # get actual team counts for each field
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            div_diffweight_list = list()
            for team_id, teamcount_list in enumerate(tfmetrics, start=1):
                refteam_sumweight_list = div_sumweight_list[dindexerGet(team_id)]['sumweight_list']
                rindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(refteam_sumweight_list)).get(x)
                diffweight_list = [{'field_id':x['field_id'],
                    'diffweight':x['count'] - \
                    refteam_sumweight_list[rindexerGet(x['field_id'])]['sumweight']}
                    for x in teamcount_list]
                div_diffweight_list.append({'team_id':team_id,
                    'diffweight_list':diffweight_list})
            connected_diffweight_list.append({'div_id':div_id,
                'div_diffweight_list':div_diffweight_list})
        cindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(
            connected_diffweight_list)).get(x)
        return _List_Indexer(connected_diffweight_list, cindexerGet)

    def IncDecFieldMetrics(self, fieldmetrics_list, findexerGet, field_id, teams, increment=True):
        ''' increment/decrement fieldmetrics_list, based on field and team (inc/dec) flag '''
        div_id = teams['div_id']
        home_id = teams[HOME]
        away_id = teams[AWAY]
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
                    # (1 in this case), that means the current team_id is favoring
                    # the use of hifield_id over lofield_id. See if it is possible
                    # to move a game between two fields if they are available on the
                    # same day
                    hifield_id = hi_use['field_id']
                    lofield_id = lo_use['field_id']
                    hi_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(hifield_id)]['slotstatus_list']
                    lo_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(lofield_id)]['slotstatus_list']
                    hi_team_metrics_list = []
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
                            (j['teams'][HOME]==team_id or j['teams'][AWAY]==team_id)]
                        if len(today_hifield_info_list) > 1:
                            logging.info("fbalancer:rebalance:today maxfieldinfo_list entry len is %d",
                                len(today_hifield_info_list))
                            #raise CodeLogicError('ftschedule:rebalance: There should only be one game per gameday')
                        if today_hifield_info_list:
                            logging.info("fbalancer:refieldbalance: div=%d hifieldday=%d lofieldday=%d hifield_id=%d lofield_id=%d",
                                div_id, hi_fieldday_id, lo_fieldday_id,
                                hifield_id, lofield_id)
                            # assuming one game per team per day when taking 0-element
                            today_hifield_info = today_hifield_info_list[0]
                            logging.debug("fbalancer:refieldbalance: hifield_id info=%s", today_hifield_info)
                            # if there is game being played on the max count field by the current team, then first find out
                            # find out how the potential time slot change associated with the field move might affect
                            #early/late time slot counters
                            isgame_list = [x['isgame'] for x in hi_ftstatus['sstatus_list']]
                            # find 0-index for last game (True) (last game may be in a different division)
                            lastTrue_slot = len(isgame_list)-1-isgame_list[::-1].index(True)
                            hi_slot = today_hifield_info['slot_index']
                            hi_teams = today_hifield_info['teams']
                            el_measure = self.timebalancer.getELcost_by_slot(
                                hi_slot, hi_teams, lastTrue_slot)
                            logging.debug('fbalancer:refieldbalance: hi_slot=%d el_measure=%d lastslot=%d',
                                hi_slot, el_measure, lastTrue_slot)
                            # Next find out who the opponent team is, then find out
                            # the field count (for the max count field and also the
                            # count for the min count field it) for that opponent
                            # team.
                            # We need the count for the opponent because it will
                            # affect it's field count if the game is moved away
                            # from the max count field
                            oppteam_id = hi_teams[HOME] if hi_teams[AWAY]==team_id else hi_teams[AWAY]
                            hifield_opp_count = self.getFieldTeamCount(tfmetrics, hifield_id, oppteam_id)
                            lofield_opp_count = self.getFieldTeamCount(tfmetrics, lofield_id, oppteam_id)
                            # the measure for opponent team - desirability to swap out this game - is just the difference
                            # between max and min field counts as the potential swap
                            # will occur from the high count field to the low count
                            # field, i.e. the larger the difference, the more
                            # benefit we will get for moving the game to the min
                            # count field.
                            opp_measure = hifield_opp_count - lofield_opp_count
                            # *****
                            # Calculate Total cost for swapping out the hifield_id game (with the designated team_id) in the
                            # current gameday.
                            # total cost = early/late swap out measure (if slot is 0 or last) +
                            # opponent team max min field count diff (opp_measure) +
                            # we might want to scale the opp_measure over the el_measure as we are focused on field
                            # balacning - leave equal weight for now
                            # Adjust cost function by subtracting 1 from
                            # opp_measure before multiplying by weight because we
                            # want a penalty to be applied if a 0 opp_measure is
                            # selected as it disrupts an already-achieved equal balance between
                            # fields
                            # Also Add in diff value, which is the measure for the
                            # current team id
                            hi_total_cost = el_measure + BALANCEWEIGHT*(opp_measure-1+diff)
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
                            logging.debug('fbalancer:refieldbalance: hifield_id team metrics=%s', hi_team_metrics)
                            # Now we are going to find all the teams (not just in this div but also all field-shared divs)
                            # using the minimum count field
                            # and then find the measures for each field - which is both the lofield_id counts for the home and
                            # away teams, along with the timeslot early/late count - el count only generated if the slot index
                            # falls under the 0 or last slot
                            # move some fields to general for loop as list comprehension gets too messy.
                            lo_sstatus_list = lo_ftstatus['sstatus_list']
                            # for current game date, find team info that has a game
                            # scheduled on the low count field
                            today_lofield_info = [{'slot_index':i,
                                'teams':j['teams']}
                                for i,j in enumerate(lo_sstatus_list) if j['isgame']]
                            lo_isgame_list = [x['isgame'] for x in lo_sstatus_list]
                            # find 0-index for last game (True) (last game may be in a different division)
                            lo_lastTrue_slot = len(lo_isgame_list)-1-lo_isgame_list[::-1].index(True)
                            for linfo in today_lofield_info:
                                lteams = linfo['teams']
                                lhome = lteams[HOME]
                                laway = lteams[AWAY]
                                ltfmetrics = fieldmetrics_list[findexerGet(lteams['div_id'])]['tfmetrics']
                                linfo['homelo_count'] = self.getFieldTeamCount(ltfmetrics, lofield_id, lhome)
                                linfo['homehi_count'] = self.getFieldTeamCount(ltfmetrics, hifield_id, lhome)
                                linfo['awaylo_count'] = self.getFieldTeamCount(ltfmetrics, lofield_id, laway)
                                linfo['awayhi_count'] = self.getFieldTeamCount(ltfmetrics, hifield_id, laway)
                                slot = linfo['slot_index']
                                # get cost associated with early/late counters, if any (0 val if not)
                                linfo['el_cost'] = self.timebalancer.getELcost_by_slot(slot, lteams, lo_lastTrue_slot)
                                # also get el counters for hifield_id teams - they might be swapped into an el slot
                                linfo['hi_teams_in_cost'] = self.timebalancer.getELcost_by_slot(slot,
                                    hi_teams, lo_lastTrue_slot, incoming=1)
                                # get the cost for the min field teams to swap into the max field slot (incoming)
                                # relevant when the hifield_id slot is an early/late slot
                                # note lastTrue_slot is for hifield_id
                                linfo['hi_slot_el_cost'] = self.timebalancer.getELcost_by_slot(
                                    hi_slot, lteams, lastTrue_slot, incoming=1)
                                # calculate min field teams to swap out from the min field slot to max field slot
                                # as the home and away teams will move away from
                                # the low count field, the best candidate is where
                                # the difference between the 'low count' field and
                                # 'high count' field is the highest (because the low
                                # count field will decrease and high count will
                                # increase - note 'low' and 'high' terms are with
                                # respect to the home and away teams that will be
                                # moving away from the high count field.  For the
                                # teams moving into the 'high count' field, the
                                # terms 'low' and 'high' may be confusing because
                                # for them the 'low count' field may actually have
                                # a higher count value than the 'high count' field)
                                homeswap_cost = linfo['homelo_count']-linfo['homehi_count']
                                awayswap_cost = linfo['awaylo_count']-linfo['awayhi_count']
                                linfo['fieldswap_cost'] = homeswap_cost + awayswap_cost
                                #***********
                                # Total cost for swapping out lofield_id matches is the sum of
                                # swap out cost for lofield_id matches + early/late cost for min field match -
                                # cost for maxf teams to come into the min field slot -
                                # cost for lofield_id teams to go into max field slot
                                #*********************
                                # subtract fieldswap_cost by 1 to add penalty if
                                # there is already balance between hi and lo count
                                # fields
                                linfo['totalswap_cost'] = BALANCEWEIGHT*(linfo['fieldswap_cost']-1) + \
                                    linfo['el_cost'] - \
                                    linfo['hi_teams_in_cost'] - linfo['hi_slot_el_cost']
                            sorted_lofield_info = sorted(today_lofield_info, key=itemgetter('totalswap_cost'), reverse=True)
                            max_linfo = max(today_lofield_info, key=itemgetter('totalswap_cost'))
                            gameday_totalcost = {'hi_fieldday_id':hi_fieldday_id,
                                'lo_fieldday_id':lo_fieldday_id,
                                'hi_slot':hi_slot, 'oppteam_id':oppteam_id,
                                'lo_slot':max_linfo['slot_index'],
                                'lo_teams':max_linfo['teams'],
                                'lo_lastTrue_slot':lo_lastTrue_slot,
                                'hi_lastTrue_slot':lastTrue_slot,
                                'total_cost':max_linfo['totalswap_cost']+hi_team_metrics['hi_total_cost']}
                            gameday_totalcost_list.append(gameday_totalcost)
                            #logging.debug('fbalancer:refieldbalance: lofield_info=%s', today_lofield_info)
                            #logging.debug('fbalancer:refieldbalance: sorted lofield_id=%s', today_lofield_info)
                            logging.debug('fbalancer:refieldbalance: max lofield_id=%s', max_linfo)
                            logging.debug('fbalancer:refieldbalance: totalcost=%s', gameday_totalcost)
                    # ******
                    # maximize cost by just taking max of total_cost on list
                    max_totalcost = max(gameday_totalcost_list, key=itemgetter('total_cost'))
                    max_hi_fieldday_id = max_totalcost['hi_fieldday_id']
                    max_lo_fieldday_id = max_totalcost['lo_fieldday_id']
                    max_oppteam_id = max_totalcost['oppteam_id']
                    max_hi_slot = max_totalcost['hi_slot']
                    max_lo_teams = max_totalcost['lo_teams']
                    max_lo_div_id = max_lo_teams['div_id']
                    max_lo_home_id = max_lo_teams[HOME]
                    max_lo_away_id = max_lo_teams[AWAY]
                    max_lo_slot = max_totalcost['lo_slot']
                    max_lo_lastTrue_slot = max_totalcost['lo_lastTrue_slot']
                    max_hi_lastTrue_slot = max_totalcost['hi_lastTrue_slot']
                    logging.debug('fbalancer:refieldbalance: totalcost_list=%s', gameday_totalcost_list)
                    logging.debug('fbalancer:refieldbalance: maximum cost info=%s', max_totalcost)

                    logging.debug('fbalancer:refieldbalance: swapping div=%d team=%d playing opponent=%d on %s hifieldday=%d to lofieldday=%d from slot=%d field=%d',
                        div_id, team_id, max_oppteam_id, common_date,
                        max_hi_fieldday_id,
                        max_lo_fieldday_id, max_hi_slot, hifield_id)
                    logging.debug('fbalancer:refieldbalance: swap with match div=%d, home=%d away=%d, slot=%d field=%d',
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
                    self.timebalancer.updateSlotELCounters(max_hi_slot, max_lo_slot, hi_teams, lo_teams,
                        lastTrue_slot1 = max_hi_lastTrue_slot,
                        lastTrue_slot2 = max_lo_lastTrue_slot)
        return True

    def ReFieldBalanceIteration(self, connected_div_list, fieldmetrics_list,
        fieldmetrics_indexerGet, commondates_list, numgames_perteam_list,
        totalmatch_tuple, divrefdistrib_tuple, teamrefdistrib_tuple):
        ''' Top level function after initial schedule is created to see if
        scheduled field distribution is balanced with respect to tminfo
        configurations and expected field distributions, both at the division
        and team level.  First measure how closely schedule meets reference target,
        and then interate until targets are met.
        '''
        min_convergence_count = VERY_LARGE
        divdiff_tuple = self.CompareDivFieldDistribution(connected_div_list,
            fieldmetrics_list, fieldmetrics_indexerGet, divrefdistrib_tuple)
        iteration_count = 1
        stuck_min_count = 0
        while iteration_count <= MAX_FIELDBALANCE_ITERATION_COUNT and \
            stuck_min_count < 10:
            logging.debug("fbalancer:refbalanceiteration at iteration=%d" % (iteration_count,))
            teamdiff_tuple = self.CompareTeamFieldDistribution(
                connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet,
                teamrefdistrib_tuple)
            logging.debug("fbalancer:refbalanceiteration: teamdif=%s" % (teamdiff_tuple.dict_list,))
            dual_list_tuple = self.identify_control_div(teamdiff_tuple)
            control_div_list = dual_list_tuple.control_div_list
            convergence_list = dual_list_tuple.convergence_list
            if not control_div_list:
                logging.info("fbalancer:refbalanceiteration ****Field Convergence achieved at iteration=%d" % (iteration_count,))
                break
            else:
                total_convergence_count = sum(x['convergence_count']
                    for x in convergence_list)
                if total_convergence_count < min_convergence_count:
                    min_convergence_count = total_convergence_count
                    stuck_min_count = 1
                elif total_convergence_count == min_convergence_count:
                    stuck_min_count += 1
                else:
                    stuck_min_count = -1
                logging.debug("fbalancer:ReFbalanceIteration: iteration count=%d stuck_min_count=%d convergence_list=%s" %
                    (iteration_count, stuck_min_count, convergence_list))
                self.apply_teamdiff_control(teamdiff_tuple, control_div_list,
                    fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
                logging.debug("fbalancer:reFbalanceiteration: fmetrics after applycontrol=%s" % (fieldmetrics_list,))
                iteration_count += 1
        else:
            logging.info("fbalancer:refbalanceiteration Field Convergence iteration Maxed out at %d without convergence" % (iteration_count,))
        return True
        '''
        old_balcount_list = self.CountFieldBalance(connected_div_list,
            fieldmetrics_list, fieldmetrics_indexerGet)
        old_bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(old_balcount_list)).get(x)
        overall_iteration_count = 1
        mindiff_count = -1
        logging.debug("fbalancer:refieldbalance: iteration=%d 1st balance count=%s",
            overall_iteration_count, old_balcount_list)
        while True:
            rebalance_count = self.ReFieldBalance(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
            balcount_list = self.CountFieldBalance(connected_div_list,fieldmetrics_list, fieldmetrics_indexerGet)
            bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(balcount_list)).get(x)
            balance_diff = [{'div_id':div_id,
                             'diff':old_balcount_list[old_bal_indexerGet(div_id)]['fcountdiff_num'] -
                             balcount_list[bal_indexerGet(div_id)]['fcountdiff_num']}
                            for div_id in connected_div_list]
            logging.debug("fbalancer:refieldbalance: continuing iteration=%d balance count=%s diff=%s",
                          overall_iteration_count, balcount_list, balance_diff)
            if all(x['diff'] < 1 for x in balance_diff):
                if mindiff_count > 0:
                    # mindiff_count counts how long we are stuck at the minimum
                    # balance diff
                    # if we already at the minimum diff, increment counter.
                    # We still want to iterate with ReFieldBalance() as there may
                    # not yet be convergence on which team_id has settled on a
                    # minimum balance diff e.g. if two or more teams are oscillating
                    # between having the min balance diff value, we should continue
                    # to iterate several more times.
                    mindiff_count += 1
                else:
                    # first time we are in min balance diff, so initialize count
                    mindiff_count = 1
            else:
                mindiff_count = -1
            if mindiff_count >= mindiff_count_max_CONST or overall_iteration_count >= field_iteration_max_CONST:
                logging.debug("fbalancer:refieldbalance: FINISHED FIELD iteration connected_div %s", connected_div_list)
                print 'finished field iteration div=', connected_div_list
                if overall_iteration_count >= field_iteration_max_CONST:
                    logging.debug("fbalancer:refieldbalance: iteration count exceeded max=%d", field_iteration_max_CONST)
                    print 'FINISHED but Iteration count > Max'
                break
            else:
                old_balcount_list = balcount_list
                old_bal_indexerGet = bal_indexerGet
                overall_iteration_count += 1
        return True
        '''

    def validate_divteam_refcount(self, divref_list, teamref_tuple):
        ''' Validate division reference field distribution list calculation
        against team reference field distribution calculation.  Aggregate of
        team reference field distribution should match distribution count
        for division reference.'''
        teamref_list = teamref_tuple.dict_list
        tindexerGet = teamref_tuple.indexerGet
        validate_flag = False
        for divref in divref_list:
            # we will make comparisons against each div_id record in the divison-
            # wide field distribution list
            div_id = divref['div_id']
            ref_distrib_list = divref['distrib_list']
            rindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(ref_distrib_list)).get(x)
            # get list of relevant fields
            field_list = [x['field_id'] for x in ref_distrib_list]
            # get distribution for team-baed field distribution refereence counts
            teamref_sw_list = teamref_list[tindexerGet(div_id)]['div_sw_list']
            if not teamref_sw_list:
                # if there is no team-based distribution for current div, skip
                # comparison and go to next div
                continue
            teamref_sum_list = [{'field_id':f,
                'sumweight':sum(x['sumweight'] for y in teamref_sw_list for x in y['sumweight_list'] if x['field_id']==f)}
                for f in field_list]
            tmindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(teamref_sum_list)).get(x)
            # format for division-wide and team-specific field distribution list
            # by example:
            # pp ref_distrib_list [{'field_id': 1, 'sumcount': 66.0}, {'field_id': 2, 'sumcount': 54.0}]
            #  pp teamref_sum_list [{'field_id': 1, 'sumweight': 66.0}, {'field_id': 2, 'sumweight': 54.0}]
            diff_sum = sum(abs(teamref_sum_list[tmindexerGet(f)]['sumweight'] -
                ref_distrib_list[rindexerGet(f)]['sumcount']) for f in field_list)
            if diff_sum > 1e-5:
                # diff_sum should be virtually 0.0; 1e-5 is just set for float
                # allowances
                raise CodeLogicError('fbalancer:validate_divteam_refcount: diff is %f divref=%s teamref=%s' %
                    (diff_sum, ref_distrib_list, teamref_sum_list))
                break
        else:
            validate_flag = True
        return validate_flag

    def calc_teamreffield_distribution_list(self, totalmatch_tuple, connected_div_list):
        ''' Calculate team-specific target distribution of number of games for each
        field in the divlist for the whole season.  Target distribtuion requires
        knowledge of game match pairups - based on game matchup use normalized
        field weights for both home and away teams; sum across all matchups to
        get expected field distribution for the whole season for the specified
        team. Sum of the expected field distribution per field, summed across
        all fields in the divlist should equal the total number of games that the
        team plays.
        Example: 6 total teams (T1 through T6, each teams plays 5 games total,
        )round robin
        3 Fields: F1, F2, F3
        AF (affinity/home field) configuration for [F1, F2, F3]:
        T1: [1,1,0]  (F1, F2 configured as home affinity)
        T2: [1,1,0]
        T3: [1,1,0]
        T4: [1,1,0]
        T5: [1,1,0]
        T6: [0,0,1]
        Above simulates a league where 5 local teams T1 thru T5 utilize F1, F2 for
        their home games;  T6 is a remote team that utilizes F3 for their home games
        If a team has multiple home field affinities, then assume the goal is to
        have an equal number of games amongst them.  So for the above, the
        weighted configuration for each team becomes:
        WT1: [0.5, 0.5, 0]
        WT2: [0.5, 0.5, 0]
        WT3: [0.5, 0.5, 0]
        WT4: [0.5, 0.5, 0]
        WT5: [0.5, 0.5, 0]
        WT6: [0,0,1]

        T1 plays matches T1vT2, T1vT3, T1vT4, T1vT5, T1vT6
        Field weights for each match involving T1:
        T1vT2: (0.5F1 + 0.5F2 + 0.5F1 + 0.5F2)/2 = 0.5F1 + 0.5F2
        T1vT3: (0.5F1 + 0.5F2 + 0.5F1 + 0.5F2)/2 = 0.5F1 + 0.5F2
        T1vT4: (0.5F1 + 0.5F2 + 0.5F1 + 0.5F2)/2 = 0.5F1 + 0.5F2
        T1vT5: (0.5F1 + 0.5F2 + 0.5F1 + 0.5F2)/2 = 0.5F1 + 0.5F2
        T1vT6: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        Aggregate over each field to get aggregate field distribution for T1:
        T1 field distribution over 5 games:
        2.25(games@)F1 + 2.25(games@)F2 + 0.5(games@)F3

        Given identical AF configs for T1 thru T5, T2 thru T5 will have the same
        field distribution as T1

        T6 matches:
        T6vT1: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        T6vT2: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        T6vT3: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        T6vT4: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        T6vT5: (0.5F1 + 0.5F2 + 1F3)/2 = 0.25F1+ 0.25F2 + 0.5F3
        Aggregate distribution for T6 over 5 games:
        1.25(games@)F1 + 1.25(games@)F2 + 2.5(games@)F3
        '''
        totalmatch_list = totalmatch_tuple.dict_list
        tindexerGet = totalmatch_tuple.indexerGet
        connected_div_sumweight_list = list()
        for div_id in connected_div_list:
            div_sumweight_list = list()
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            totalteams = divinfo['totalteams']
            # get match information for the division
            match_list = totalmatch_list[tindexerGet(div_id)]['match_list']
            tmindex_list = self._tminfo_indexerMatch(div_id)
            if tmindex_list:
                divtminfo_list = [self._tminfo_list[index] for index in tmindex_list]
                tmindexerGet = lambda x: dict((p['tm_id'],i) for i,p in enumerate(divtminfo_list)).get(x)
                for team_id in range(1, totalteams+1):
                    # iterate through each team
                    #reftminfo = self._tminfo_list[self._tminfo_indexerGet((div_id, team_id))]
                    reftminfo = divtminfo_list[tmindexerGet(team_id)]
                    reftm_effweight_list = reftminfo['effweight_list']
                    eff_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(reftm_effweight_list)).get(x)
                    # get list of opponents that team_id plays across season
                    opponent_list = self.get_opponent_list(match_list, team_id)
                    # get the effective (normalized) weight list for each field for
                    # each opponent in the opponent list
                    opponent_weight_list = [{'opp_id':opp_id, 'effweight_list':self._tminfo_list[self._tminfo_indexerGet((div_id, opp_id))]['effweight_list']} for opp_id in opponent_list]
                    # initialize weight sum list that we are going to compute for earch
                    # reference team_id; establish season cumulative weights for
                    # specified team for each field
                    reftm_sumweight_list = list()
                    # rem indexerGet lambda gets evaluated at run-time when
                    # reftm_sumweight_list is an actual list w contents
                    reftm_sw_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(reftm_sumweight_list)).get(x)
                    for opponent_weight_dict in opponent_weight_list:
                        # iterate through weight list data for each opponent
                        # get the effective weight information for each field relevant
                        # to the current specified opponent
                        opp_effweight_list = opponent_weight_dict['effweight_list']
                        for opp_effweight_dict in opp_effweight_list:
                            field_id = opp_effweight_dict['field_id']
                            opp_effweight = opp_effweight_dict['effweight']
                            # get effective weight information for current reference
                            # team
                            reftm_effweight = reftm_effweight_list[eff_indexerGet(field_id)]['effweight']
                            # we always average out the field weight contributions
                            # from the reference and current opponent id
                            field_effweight = (reftm_effweight+opp_effweight)*0.5
                            reftm_sw_index = reftm_sw_indexerGet(field_id)
                            if reftm_sw_index is not None:
                                # if index for field_id already exists, then we need to
                                # add to the running sum of the effective weight for
                                # that field_id
                                reftm_sumweight_list[reftm_sw_index]['sumweight'] += field_effweight
                            else:
                                reftm_sumweight_list.append({'field_id':field_id,
                                    'sumweight':field_effweight})
                    div_sumweight_list.append({'team_id':team_id,
                        'sumweight_list':reftm_sumweight_list})
            else:
                # infex list from tminfo should always exist as we also created
                # default tminfo even when tminfo is not configured and not read
                # from db
                raise CodeLogicError("fbalancer:tmfino_list not detected")
            connected_div_sumweight_list.append({'div_id':div_id,
                'div_sw_list':div_sumweight_list})
            cindexerGet = lambda x: dict((p['div_id'],i)
                for i,p in enumerate(connected_div_sumweight_list)).get(x)
        return _List_Indexer(connected_div_sumweight_list, cindexerGet)

    def get_opponent_list(self, match_list, team_id):
        '''Given team_id, find non-unique opponents throughout season.  If team
        plays an opponent multiple times, list that opponent as many times as
        they are played. '''
        opponent_list = list()
        for perround_data in match_list:
            perround_game_list = perround_data[GAME_TEAM]
            for game in perround_game_list:
                if game['HOME'] == team_id:
                    opponent_list.append(game['AWAY'])
                    break
                if game['AWAY'] == team_id:
                    opponent_list.append(game['HOME'])
                    break
        return opponent_list
