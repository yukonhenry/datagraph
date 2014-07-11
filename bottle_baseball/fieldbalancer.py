''' Copyright YukonTR 2013 '''
from datetime import  datetime
from schedule_util import all_value, enum, shift_list, \
    all_isless, find_ge, find_le
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
import logging
from operator import itemgetter
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, \
     CodeLogicError, SchedulerConfigurationError
from math import ceil, floor
from collections import namedtuple

home_CONST = 'HOME'
away_CONST = 'AWAY'
balanceweight_CONST = 2
field_iteration_max_CONST = 15
mindiff_count_max_CONST = 4
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class FieldBalancer:
    def __init__(self, divinfo_tuple, fstatus_tuple, timebalancer):
        self.divinfo_list = divinfo_tuple.dict_list
        self.divinfo_indexerGet = divinfo_tuple.indexerGet
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        self.timebalancer = timebalancer

    def findMinimumCountField(self, homemetrics_list, awaymetrics_list, rd_fieldcount_list, reqslots_perrnd_num, hf_list, field_list, aggregnorm_tuple, divrefdistrib_tuple, teamrefdistrib_tuple, submin=0):
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
        if hf_list:
            home_hf_set = set(hf_list[0]) if hf_list[0] else set(field_list)
            away_hf_set = set(hf_list[1]) if hf_list[1] else set(field_list)
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
        # field counter for home team
        eff_homemetrics_list = [x for x in homemetrics_list
            if x['field_id'] in hfunion_set]
        # field counter for away team
        eff_awaymetrics_list = [x for x in awaymetrics_list
            if x['field_id'] in hfunion_set]
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
            logging.info("ftscheduler:findMinCountField: field=%d maxed out, required=%s ind=%d penalty=%d",
                         maxedout_field, maxdiff_dict, maxedout_ind, penalty)
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
            logging.info("ftscheduler:findMinCountField: field=%d Almost Target, required=%s ind=%d",
                almostmaxed_field, maxdiff_dict, almost_ind)
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

    def getFieldTeamCount(self, tfmetrics, field_id, team_id):
        ''' get field count for team specified - extracted from tfmetrics (teamfieldmetrics extracted by
        div_id from fieldmetrics_list '''
        metrics_list = tfmetrics[team_id-1]
        metrics_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(metrics_list)).get(x)
        count = metrics_list[metrics_indexerGet(field_id)]['count']
        return count

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
            # for each field get difference - acutal-reference
            diff_distrib_list = [{'field_id':f,
                'diffcount':actual_distrib_list[aindexerGet(f)]['sumcount'] -
                ref_distrib_list[rindexerGet(f)]['sumcount']} for f in field_list]
            actualref_diff_list.append({'div_id':div_id,
                'distrib_list':diff_distrib_list})
        aindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(actualref_diff_list)).get(x)
        return _List_Indexer(actualref_diff_list, aindexerGet)

    def identify_control_div(self, divdiff_tuple):
        ''' return divisions that have any diffcount greater than 1
        '''
        divdiff_list = divdiff_tuple.dict_list
        '''
        correction_div_list = list()
        for divdiff in divdiff_list:
            distrib_list = divdiff['distrib_list']
            if any(abs(x['diffcount']) > 1.0 for x in distrib_list):
                correction_div_list.append(divdiff['div_id'])
        '''
        control_div_list = [x['div_id'] for x in divdiff_list
            if any(abs(y['diffcount']) > 1.0 for y in x['distrib_list'])]
        return control_div_list

    def apply_teamdiff_control(self, teamdiff_tuple, cdiv_list, fmetrics_list,
        findexerGet, commondates_list):
        teamdiff_list = teamdiff_tuple.dict_list
        tindexerGet = teamdiff_tuple.indexerGet
        # get div_id's covered in teamdiff_list - it may be a proper subset of
        # cdiv_list
        td_div_list = [x['div_id'] for x in teamdiff_list]
        # div_id's to iterate through is intersection of cdiv_list and td_div_list
        # note td_div shoudl always be a proper subset of cdiv
        div_set = set.intersection(set(td_div_list), set(cdiv_list))
        for div_id in div_set:
            # get list of team diff weights for specified division
            divteam_diffweight_list = teamdiff_list[tindexerGet(div_id)]['div_diffweight_list']
            dtindexerGet = lambda x: dict((p['team_id'],i)
                for i,p in enumerate(divteam_diffweight_list)).get(x)
            # get current field count metrics for specified div_id
            tfmetrics = fmetrics_list[findexerGet(div_id)]['tfmetrics']
            for team_diffweight in divteam_diffweight_list:
                # iterate through each team_id and it's diff weight list
                # get reference team id and it's diffweights for each field
                team_id = team_diffweight['team_id']
                diffweight_list = team_diffweight['diffweight_list']
                # sort diffweights from highest to lowest
                sorted_diffweight_list = sorted(diffweight_list,
                    key=itemgetter("diffweight"), reverse=True)
                # get maximum and minimum diff weights for specified team_id
                # and their corresponding field_id's
                # NOTE we will need to generalize from just working with the
                # max and min diffweights and field_id's to working through the
                # entire diffweight_list to find the optimal swap.
                max_dict = sorted_diffweight_list[0]
                max_diffweight = max_dict['diffweight']
                if max_diffweight > 0.99:
                    max_field_id = max_dict['field_id']
                    max_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(max_field_id)]['slotstatus_list']
                    max_indexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(max_ftstatus_list)).get(x)
                min_dict = sorted_diffweight_list[len(sorted_diffweight_list)-1]
                min_field_id = min_dict['field_id']
                min_diffweight = min_dict['diffweight']
                # get max and min slot status lists and corresponding indexerget
                # functions

                min_ftstatus_list = self.fieldstatus_list[self.fstatus_indexerGet(min_field_id)]['slotstatus_list']
                min_indexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(min_ftstatus_list)).get(x)
                for commondates_dict in commondates_list:
                    # get fieldday_id that corresponds to field_id for current
                    # common date; commondates_dict[map_dict] key:value is
                    # field_id:fielday_id
                    max_fieldday_id = commondates_dict['map_dict'][max_field_id]
                    min_fieldday_id = commondates_dict['map_dict'][min_field_id]
                    # get fieldstatus list for the max and min fieldday_id
                    max_ftstatus = max_ftstatus_list[max_indexerGet(max_fieldday_id)]
                    min_ftstatus = min_ftstatus_list[min_indexerGet(min_fieldday_id)]
                    # see if the reference team is playing on the max_field_id on
                    # the current game date.  If so, get game data.
                    max_fieldmatch_list = [{'slot_index':i,
                        'start_time':j['start_time'], 'teams':j['teams']}
                        for i,j in enumerate(max_ftstatus['sstatus_list'])
                        if j['isgame'] and j['teams']['div_id']==div_id and
                        (j['teams'][home_CONST]==team_id or
                            j['teams'][away_CONST]==team_id)]
                    if max_fieldmatch_list:
                        # NOTE: assume there is only one game per day, but need to
                        # generalize
                        max_fieldmatch = max_fieldmatch_list[0]
                        max_teams = max_fieldmatch['teams']
                        # get information necessary to determine early/late slot
                        # costs
                        max_isgame_list = [x['isgame'] for x in max_ftstatus['sstatus_list']]
                        max_lastTrue_slot = len(max_isgame_list)-1-max_isgame_list[::-1].index(True)
                        # get early/late cost from current scheduled slot for
                        # reference team
                        max_el_measure = self.timebalancer.getELcost_by_slot(
                            max_fieldmatch['slot_index'], max_teams,
                            max_lastTrue_slot)
                        oppteam_id = max_teams[home_CONST] if max_teams[away_CONST]==team_id else max_teams[away_CONST]
                        oppmax_field_count = self.getFieldTeamCount(tfmetrics, max_field_id, oppteam_id)
                        oppmin_field_count = self.getFieldTeamCount(tfmetrics, min_field_id, oppteam_id)
    def CompareTeamFieldDistribution(self, connected_div_list, fieldmetrics_list,
        findexerGet, tmref_tuple):
        ''' Get actual-reference (minus, subtraction) for field distribution
        counts at the per-team level '''
        tmref_list = tmref_tuple.dict_list
        tindexerGet = tmref_tuple.indexerGet
        connected_diffweight_list = list()
        for div_id in connected_div_list:
            # get team reference
            div_sumweight_list = tmref_list[tindexerGet(div_id)]['div_sw_list']
            if not div_sumweight_list:
                # if no team weight list for current division, skip comparison and
                # go to next div_id
                continue
            dindexerGet = lambda x: dict((p['team_id'],i) for i,p in enumerate(div_sumweight_list)).get(x)
            # get actual team counts for each field
            tfmetrics = fieldmetrics_list[findexerGet(div_id)]['tfmetrics']
            div_diffweight_list = list()
            for team_id, actualtm_count_list in enumerate(tfmetrics, start=1):
                reftm_sumweight_list = div_sumweight_list[dindexerGet(team_id)]['sumweight_list']
                rindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(reftm_sumweight_list)).get(x)
                diffweight_list = [{'field_id':x['field_id'],
                    'diffweight':x['count'] -
                    reftm_sumweight_list[rindexerGet(x['field_id'])]['sumweight']}
                    for x in actualtm_count_list]
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
                    # (1 in this case), that means the current team_id is favoring
                    # the use of hifield_id over lofield_id. See if it is possible
                    # to move a game between two fields if they are available on the
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
                            el_measure = self.timebalancer.getELcost_by_slot(
                                hi_slot, hi_teams, lastTrue_slot)
                            logging.debug('ftscheduler:refieldbalance: hi_slot=%d el_measure=%d lastslot=%d',
                                hi_slot, el_measure, lastTrue_slot)
                            # Next find out who the opponent team is, then find out
                            # the field count (for the max count field and also the
                            # count for the min count field it) for that opponent
                            # team.
                            # We need the count for the opponent because it will
                            # affect it's field count if the game is moved away
                            # from the max count field
                            oppteam_id = hi_teams[home_CONST] if hi_teams[away_CONST]==team_id else hi_teams[away_CONST]
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
                            # selected as it disrupts an equal balance between
                            # fields
                            # Also Add in diff value, which is the measure for the
                            # current team id
                            hi_total_cost = el_measure + balanceweight_CONST*(opp_measure-1+diff)
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
                                lhome = lteams[home_CONST]
                                laway = lteams[away_CONST]
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
                                linfo['totalswap_cost'] = balanceweight_CONST*(linfo['fieldswap_cost']-1) + \
                                    linfo['el_cost'] - \
                                    linfo['hi_teams_in_cost'] - linfo['hi_slot_el_cost']
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
                    self.timebalancer.updateSlotELCounters(max_hi_slot, max_lo_slot, hi_teams, lo_teams,
                        lastTrue_slot1 = max_hi_lastTrue_slot,
                        lastTrue_slot2 = max_lo_lastTrue_slot)
                #team_id += 1
        return rebalance_count

    def ReFieldBalanceIteration(self, connected_div_list, fieldmetrics_list,
        fieldmetrics_indexerGet, commondates_list, numgames_perteam_list,
        totalmatch_tuple, divrefdistrib_tuple, teamrefdistrib_tuple):
        ''' Top level function after initial schedule is created to see if
        scheduled field distribution is balanced with respect to tminfo
        configurations and expected field distributions, both at the division
        and team level.  First measure how closely schedule meets reference target,
        and then interate until targets are met.
        divrefdistrib_tuple and divdiff_tuple will exist even if tminfo is not
        configured and we are targetin an all-equal-field distribution
        '''
        divdiff_tuple = self.CompareDivFieldDistribution(connected_div_list,
            fieldmetrics_list, fieldmetrics_indexerGet, divrefdistrib_tuple)
        if teamrefdistrib_tuple:
            # if teamrefdistrib_tuple exists, ensure reference field distribution
            # count - one for div-level, and the other for team-level - is
            # consistent between the two
            validate_flag = self.validate_divteam_refcount(divrefdistrib_tuple,
                teamrefdistrib_tuple)
            if validate_flag:
                teamdiff_tuple = self.CompareTeamFieldDistribution(
                    connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet,
                    teamrefdistrib_tuple)
                control_div_list = self.identify_control_div(divdiff_tuple)
                #self.apply_teamdiff_control(teamdiff_tuple, control_div_list,
                #    fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
            else:
                raise CodeLogicError(
                    "ftscheduler:ReFieldBalanceIteration:validation between div and team ref counts failed")
        old_balcount_list = self.CountFieldBalance(connected_div_list,
            fieldmetrics_list, fieldmetrics_indexerGet)
        old_bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(old_balcount_list)).get(x)
        overall_iteration_count = 1
        mindiff_count = -1
        logging.debug("ftscheduler:refieldbalance: iteration=%d 1st balance count=%s",
            overall_iteration_count, old_balcount_list)
        while True:
            rebalance_count = self.ReFieldBalance(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet, commondates_list)
            balcount_list = self.CountFieldBalance(connected_div_list,fieldmetrics_list, fieldmetrics_indexerGet)
            bal_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(balcount_list)).get(x)
            balance_diff = [{'div_id':div_id,
                             'diff':old_balcount_list[old_bal_indexerGet(div_id)]['fcountdiff_num'] -
                             balcount_list[bal_indexerGet(div_id)]['fcountdiff_num']}
                            for div_id in connected_div_list]
            logging.debug("ftscheduler:refieldbalance: continuing iteration=%d balance count=%s diff=%s",
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
                logging.debug("ftscheduler:refieldbalance: FINISHED FIELD iteration connected_div %s", connected_div_list)
                print 'finished field iteration div=', connected_div_list
                if overall_iteration_count >= field_iteration_max_CONST:
                    logging.debug("ftscheduler:refieldbalance: iteration count exceeded max=%d", field_iteration_max_CONST)
                    print 'FINISHED but Iteration count > Max'
                break
            else:
                old_balcount_list = balcount_list
                old_bal_indexerGet = bal_indexerGet
                overall_iteration_count += 1
        return True

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

    def validate_divteam_refcount(self, divref_tuple, teamref_tuple):
        ''' Validate division reference field distribution list calculation
        against team reference field distribution calculation.  Aggregate of
        team reference field distribution should match distribution count
        for division reference.'''
        divref_list = divref_tuple.dict_list
        dindexerGet = divref_tuple.indexerGet
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
                raise CodeLogicError('ftscheduler:validate_divteam_refcount: diff is %f divref=%s teamref=%s' %
                    (diff_sum, ref_distrib_list, teamref_sum_list))
                break
        else:
            validate_flag = True
        return validate_flag
