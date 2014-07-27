''' Copyright YukonTR 2013 '''
from datetime import  datetime, timedelta
from itertools import chain
from schedule_util import roundrobin, enum, shift_list, \
    getConnectedDivisionGroup, all_isless, find_ge, find_le
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
from timebalancer import TimeBalancer
from fieldbalancer import FieldBalancer
from conflictprocess import ConflictProcess

home_CONST = 'HOME'
away_CONST = 'AWAY'
game_team_CONST = 'GAME_TEAM'
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python
date_format_CONST = '%m/%d/%Y'

#https://docs.python.org/2/library/datetime.html
_absolute_earliest_time = parser.parse('05:00').time()
_absolute_earliest_date = parser.parse('01/01/2010').date()

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class FieldTimeScheduleGenerator:
    def __init__(self, dbinterface, divinfo_tuple, fieldinfo_tuple,
        prefinfo_triple=None, pdbinterface=None, tminfo_tuple=None,
        conflictinfo_list=None, cdbinterface=None):
        self.divinfo_list = divinfo_tuple.dict_list
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
            self.pdbinterface = pdbinterface
        else:
            self.prefinfo_list = None
            self.prefinfo_indexerGet = None
            self.prefinfo_indexerMatch = None
            self.pdbinterface = None
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
            self.tminfo_indexerGet = None
            self.tminfo_indexerMatch = None
        self.conflictinfo_list = conflictinfo_list
        if conflictinfo_list:
            self.conflictprocess_obj = ConflictProcess(conflictinfo_list,
                divinfo_tuple, cdbinterface)
            self.cdbinterface = cdbinterface
        else:
            self.conflictprocess_obj = None
        # get connected divisions through shared fields
        self.connected_div_components = getConnectedDivisionGroup(
            self.fieldinfo_list, key='primaryuse_list')
        fstatus_tuple = self.getFieldSeasonStatus_list()
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet
        #logging.debug("fieldseasonstatus init=%s",self.fieldstatus_list)
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.divinfo_list)+1):
            self.total_game_dict[i] = []
        self.dbinterface = dbinterface
        # timegap_list tracks the last scheduled gametime for each team, which is
        # used to calculate the earliest candidate gametime for the next game while
        # honoring the minimum gap time between consecutive games.
        self.timegap_list = []
        self.timegap_indexerMatch = None
        self.timebalancer = TimeBalancer(fstatus_tuple)
        self.fieldbalancer = FieldBalancer(divinfo_tuple, fstatus_tuple,
            tminfo_tuple, self.timebalancer)
        wtuple = self.init_homefieldweight_list()
        self.homefield_weight_list = wtuple.dict_list
        self.hfweight_indexerGet = wtuple.indexerGet

    def generateSchedule(self, totalmatch_tuple):
        totalmatch_list = totalmatch_tuple.dict_list
        totalmatch_indexerGet = totalmatch_tuple.indexerGet
        self.checkFieldAvailability(totalmatch_tuple)
        self.dbinterface.dropgame_docs()  # drop current schedule collection
        EL_enum = self.timebalancer.EL_enum
        # work with each set of connected divisions w. shared field
        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            submatch_list = []
            gameinterval_dict = {}
            # note following counters can be initialized within the connected_div_components
            # loop because the divisions are completely isolated from each other
            # outside of the inner div_id/connected_div_list loop below
            # fieldmetrics_list tracks per-team field counts
            fieldmetrics_list = []
            divtotal_el_list = []
            matchlist_len_list = []
            # take one of those connected divisions and iterate through each division
            numgames_perteam_list = list()
            reqslots_perrnd_num = 0
            # in addition to fieldstatus_list, which tracks scheduled games
            # by field and time slot, track schedule by div_id and team_id
            connected_sched_list = list()
            conindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(connected_sched_list)).get(x)
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
                numgames_perteam_list.append({'div_id':div_id,
                    'numgames_list':divmatch_dict['numgames_perteam_list']})
                reqslots_perrnd_num += divmatch_dict['gameslots_perrnd_perdiv']
                fmetrics_list = [{'field_id':x, 'count':0} for x in divfield_list]
                # note below totalteams*[fmetrics_list] only does a shallow copy; use deepcopy
                tfmetrics_list = [deepcopy(fmetrics_list) for i in range(totalteams)]
                fieldmetrics_list.append({'div_id':div_id, 'tfmetrics':tfmetrics_list})
                # get metrics and counters for time balancing:
                divtarget_el = self.timebalancer.get_divtarget_el(
                    self.divinfo_tuple, self.fieldinfo_list, div_id,
                    div_totalgamedays)
                # per team fair share of early or late time slots
                teamtarget_el = int(ceil(divtarget_el/totalteams))  # float value
                # calculate each team's target share of early and late games
                earlylate_list = [{'early':teamtarget_el, 'late':teamtarget_el} for i in range(totalteams)]
                self.timebalancer.target_earlylate_list.append({'div_id':div_id, 'target_list':earlylate_list})
                # each division's target share of early and late games
                # we have this metric because we are using 'ceil' for the team target so not every team
                # will have to meet requirements
                # Changed, 8/2/13 to 'round' - as round better preserves the
                # divtotal requirements for the connected divisions group.
                # We want
                # numdivision*gamesperseason*2*totalnumfield_in_connected_div
                # factor 2 above is due to double credit because each game involves two teams
                divtotal_el_list.append({'div_id':div_id,
                    'early':int(round(divtarget_el)),
                    'late':int(round(divtarget_el))})
                #initialize early late slot counter
                counter_list = [{'early':0, 'late':0} for i in range(totalteams)]
                self.timebalancer.current_earlylate_list.append({'div_id':div_id, 'counter_list':counter_list})
                # init time gap list element for current div
                # 'last_day' is last gameday, 'last_time' is last gametime
                self.timegap_list.extend([{'div_id':div_id,
                    'last_date':_absolute_earliest_date,
                    'last_endtime':-1, 'team_id':x}
                    for x in range(1, totalteams+1)])
                connected_sched_list.append({'div_id':div_id,
                    'sched_list':list()})
            logging.debug('ftscheduler: target early late games=%s divtotal target=%s',
                self.timebalancer.target_earlylate_list, divtotal_el_list)
            # we are assuming still below that all fields in fset are shared by the field-sharing
            # divisions, i.e. we are not sufficiently handing cases where div1 uses fields [1,2]
            # and div2 is using fields[2,3] (field 2 is shared but not 1 and 3)

            fieldmetrics_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(fieldmetrics_list)).get(x)
            divtotalel_indexer =  dict((p['div_id'],i) for i,p in enumerate(divtotal_el_list))
            cel_indexerGet = self.timebalancer.cel_indexerGet
            tel_indexerGet = self.timebalancer.tel_indexerGet
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
            # get normalized field weights aggregated over all divisions in the
            # connected_div_list
            aggregnorm_tuple = self.get_aggregnorm_hfweight_list(connected_div_list)
            # get the reference (target) field distribution counts for this
            # division.  Count value is a float and may have fractional
            # component.
            # first get per-div field distribution list (there will always be a
            # non-null return value)
            divrefdistrib_tuple = self.calc_divreffield_distribution_list(
                numgames_perteam_list)
            divrefdistrib_list = divrefdistrib_tuple.dict_list
            drindexerGet = divrefdistrib_tuple.indexerGet
            # get per-team field distribution list - return may be null if
            # af_list was not configured for any division
            teamrefdistrib_tuple = self.fieldbalancer.calc_teamreffield_distribution_list(
                totalmatch_tuple, connected_div_list)
            teamrefdistrib_list = teamrefdistrib_tuple.dict_list
            # indexerGet is to get div_id subcomponent
            trindexerGet = teamrefdistrib_tuple.indexerGet
            if not self.fieldbalancer.validate_divteam_refcount(divrefdistrib_list,
                teamrefdistrib_tuple):
                raise CodeLogicError("ftscheduler:generateSchedule: per-div and per-team reference count calc are not consistent per-div %s per-team  %s" % (divrefdistrib_list, teamrefdistrib_list))
                return False
            for round_id in range(1,max(matchlist_len_list)+1):
                # counters below count how many time each field is used for every
                # round; reset for each round/gameday
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
                    hfindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list)).get(x)
                    afindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list)).get(x)
                    tel_index = tel_indexerGet(div_id)
                    target_el_list = self.timebalancer.target_earlylate_list[tel_index]['target_list']
                    home_targetel_dict = target_el_list[home_id-1]
                    away_targetel_dict = target_el_list[away_id-1]
                    cel_index = cel_indexerGet(div_id)
                    current_el_list = self.timebalancer.current_earlylate_list[cel_index]['counter_list']
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
                    # hf_list will be a two-element list, with each elem a dict
                    # containing team_id and af_list information
                    # Note there are many cases where hf_list will be None or even
                    # if hf_list is a list, one or both elements may be None
                    if self.tminfo_indexerMatch and \
                        self.tminfo_indexerMatch(div_id):
                        hf_list = []
                        for team_id in [home_id, away_id]:
                            tmindex = self.tminfo_indexerGet((div_id, team_id))
                            # remember append order follows idtype iteration
                            hf_list.append({'team_id': team_id,
                                'af_list':self.tminfo_list[tmindex]['af_list'] if tmindex is not None else None})
                    else:
                        hf_list = None
                    # Finding the initial venue/time assignament for the current
                    # round is done in two steps:  First producing a list of
                    # candidate fields, in prioritized order.  Next determining
                    # the earliest date within the current round that matches
                    # field availability, and then determining the optimal time
                    # slot.
                    # ----------------------------------
                    divteamref_list = teamrefdistrib_list[trindexerGet(div_id)]['div_sw_list']
                    # also get div reference count info
                    divref_list = divrefdistrib_list[drindexerGet(div_id)]['distrib_list']
                    sumsortedfield_list = self.fieldbalancer.findMinimumCountField(
                        home_fieldmetrics_list, away_fieldmetrics_list,
                        rd_fieldcount_list, reqslots_perrnd_num, hf_list,
                        field_list, aggregnorm_tuple, divref_list, divteamref_list)
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
                            prioritized_list = self.prioritizefield_list(datefield_list, sumsortedfield_list,
                                key="sumdiffcount")
                            for p_dict in prioritized_list:
                                # go through the ordered list of fields
                                field_id = p_dict['field_id']
                                fieldday_id = p_dict['fieldday_id']
                                slot_index = self.timebalancer.findconfirm_slot(
                                    field_id, fieldday_id, home_currentel_dict,
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
                            slot_index = self.timebalancer.findconfirm_slot(
                                field_id, fieldday_id, home_currentel_dict,
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
                    home_fieldmetrics_list[hfindexerGet(field_id)]['count'] += 1
                    away_fieldmetrics_list[afindexerGet(field_id)]['count'] += 1
                    rd_fieldcount_list[rd_fieldcount_indexerGet(field_id)]['count'] += 1
                    self.updatetimegap_list(div_id, home_id, away_id, game_date,
                        gametime+gameinterval)
                    div = self.divinfo_list[self.divinfo_indexerGet(div_id)]
                    sched_list = connected_sched_list[conindexerGet(div_id)]['sched_list']
                    # populate sched_list, which is an in-memory store of sched
                    # for the current connected_div_list
                    # start_time is a dt object
                    sched_list.append({'game_date':game_date,
                        'start_time':gametime, 'home_id':home_id,
                        'away_id':away_id, 'field_id':field_id,
                        'fieldday_id':fieldday_id})
                    logging.info("div=%s%s home=%d away=%d round_id=%d, date=%s fieldday_id=%d field=%d gametime=%s slotindex=%d",
                        div['div_age'], div['div_gen'], home_id, away_id, round_id,
                        game_date, fieldday_id, field_id, gametime.time(),
                        slot_index)
                    logging.info("-----to next game------")
                logging.debug("ftscheduler: divlist=%s end of round=%d rd_fieldcount_list=%s",
                              connected_div_list, round_id, rd_fieldcount_list)
            # First cut correct schedule is complete at this point, but re-measure
            # and re-iterate on field balance/distribution
            self.fieldbalancer.ReFieldBalanceIteration(connected_div_list,
                fieldmetrics_list,
                fieldmetrics_indexerGet, commondates_list, numgames_perteam_list,
                totalmatch_tuple, divrefdistrib_tuple, teamrefdistrib_tuple)
            # and then work on time rebalanceing
            self.timebalancer.ReTimeBalance(fset, connected_div_list)
            self.ManualSwapTeams(fset, connected_div_list)
            if self.conflictprocess_obj:
                if self.prefinfo_list:
                    pref_len = len(self.prefinfo_list)
                else:
                    pref_len = 0
                conflictpref_list = self.conflictprocess_obj.process(connected_div_list,
                    connected_sched_list, conindexerGet, pref_len)
                if self.prefinfo_list:
                    # if prefinfo_list already exists, then concatenate to it
                    self.prefinfo_list.extend(conflictpref_list)
                else:
                    # if no prefinfo_list exists, then extend to it
                    self.prefinfo_list = conflictpref_list
                    # we also need to create indexerGet and indexerMatch
                    self.prefinfo_indexerGet = lambda x: dict((p['pref_id'],i)
                        for i,p in enumerate(self.prefinfo_list)).get(x)
                    self.prefinfo_indexerMatch = lambda x: [i for i,p in
                        enumerate(self.prefinfo_list) if p['div_id'] == x]
            if self.prefinfo_list:
                status_list_tuple = self.ProcessPreferences(fset,
                    connected_div_list)
                constraint_status_list = status_list_tuple.constraint
                conflict_status_list = status_list_tuple.conflict
                if self.pdbinterface:
                    self.pdbinterface.write_constraint_status(
                        constraint_status_list)
                if conflict_status_list:
                    self.cdbinterface.write_conflict_status(conflict_status_list)
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

    def updatetimegap_list(self, div_id, home, away, game_date, endtime):
        ''' update self.timegap_list entries with latest scheduled games '''
        for team in (home, away):
            teamgap_dict = self.timegap_list[self.timegap_indexerMatch((div_id, team))[0]]
            # game_date comes in as a datetime obj so covert to dateobj
            teamgap_dict['last_date'] = game_date.date()
            teamgap_dict['last_endtime'] = endtime.time()
        return True

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
        in as second parameter.  Assume list is already sorted in desired order
        '''
        #key_list = sorted([x[key] for x in sortedinput_list])
        key_list = [x[key] for x in sortedinput_list]
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
        cel_indexerGet = self.timebalancer.cel_indexerGet
        tel_indexerGet = self.timebalancer.tel_indexerGet
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
                    cel_counter_list = self.timebalancer.current_earlylate_list[cel_indexerGet(swapdiv_id)]['counter_list']
                    tel_target_list = self.timebalancer.target_earlylate_list[tel_indexerGet(swapdiv_id)]['target_list']
                    # counter swaps
                    cel_counter_list[team1_id-1], cel_counter_list[team2_id-1] = \
                        cel_counter_list[team2_id-1], cel_counter_list[team1_id-1]
                    tel_target_list[team1_id-1], tel_target_list[team2_id-1] = \
                        tel_target_list[team2_id-1], tel_target_list[team1_id-1]

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

    def ProcessPreferences(self, fset, div_set):
        ''' process specified team constraints - see leaguedivprep data structure'''
        constraint_status_list = list()
        conflict_status_list = list()
        confl_indexerGet = lambda x: dict((p['conflict_id'],i) for i,p in enumerate(conflict_status_list)).get(x)
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
                    if 'conflict_id' in constraint:
                        # preferences are generated  from conflict list in
                        # conflictprocess_obj.process()
                        conflict_id = constraint['conflict_id']
                        start_after_dt = constraint['start_after_dt']
                        end_before_dt = constraint['end_before_dt']
                        cgame_date = constraint['game_date']
                    else:
                        # preference info generated from UI config
                        start_after_str = constraint.get('start_after')
                        start_after_dt = parser.parse(start_after_str)
                        end_before_str = constraint.get('end_before')
                        end_before_dt = parser.parse(end_before_str)
                        cgame_date = parser.parse(constraint['game_date']).date()
                    break_flag = False
                    swapmatch_list = []
                    for f in fset:
                        # reassign cstartafter_dt, cendbefore_time in case  it
                        # was nulled out in previous loop
                        cstartafter_time = start_after_dt
                        cendbefore_time = end_before_dt
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
                                    logging.debug("ftscheduler:processprefs: constraint %d is not needed since start_after=end_before",
                                        cpref_id)
                                    continue # go to the next field in fset
                            else:
                                logging.debug("ftscheduler:processprefs: constraint %d nothing specified",
                                    cpref_id)
                                continue
                            # first
                            # search through each field for the divset to 1)find if team is already scheduled in a desired slot; or
                            # 2) if not, find the list of matches that the team can swap with during that day
                            fstatus = self.fieldstatus_list[self.fstatus_indexerGet(f)]
                            #fslots_num = fstatus['slotsperday']
                            fsstatus_list =  fstatus['slotstatus_list'][cmapfieldday_id-1]['sstatus_list']
                            # getting len of current fsstatus_list more accurate
                            # than using slotsperday value
                            fslots_num = len(fsstatus_list)
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
                                logging.debug("ftscheduler:processprefs:candidate matches in field=%d constraint=%d for swap %s",
                                              f, cpref_id, swapmatch_list)
                                continue # to next field_id in fset loop
                            break  # from outer for fset loop
                        else:
                            # if calendarmap does not produce a gamedate match
                            continue
                    if break_flag:
                        if 'conflict_id' in locals():
                            logging.debug("ftscheduler:processprefs: conflict id %d pref_id %d already satisfied" %
                                (conflict_id, cpref_id))
                            cindex = confl_indexerGet(conflict_id)
                            if cindex is not None:
                                # conflict_id entry already exists
                                conflict_status_list[cindex]['count'] += 1
                            else:
                                conflict_status_list.append(
                                    {'conflict_id':conflict_id, 'count':1})
                        else:
                            logging.debug("ftscheduler:processprefs: id %d already satisfied as is", cpref_id)
                            print '*********preference ', cpref_id, 'is already satisfied'
                            constraint_status_list.append({'pref_id':cpref_id,
                                'status':1})
                    else:
                        logging.debug("ftscheduler:processprefs: pref id=%d  candidate swap=%s",
                            cpref_id, swapmatch_list)
                        print '####preference', cpref_id
                        status_int = self.findMatchSwapForConstraint(fset, cdiv_id, cteam_id, cgame_date, cpriority, swapmatch_list)
                        if 'conflict_id' in locals():
                            cindex = confl_indexerGet(conflict_id)
                            if cindex is not None:
                                # conflict_id entry already exists
                                # status_int has a value of 0 or 1
                                conflict_status_list[cindex]['count'] += status_int
                            else:
                                # add first entry for conflict_id in confict status
                                # list - init value will be 0 or 1
                                conflict_status_list.append(
                                    {'conflict_id':conflict_id, 'count':status_int})
                        else:
                            constraint_status_list.append({'pref_id':cpref_id,
                                'status':status_int})
        status_list_tuple = namedtuple('status_list_tuple', 'constraint conflict')
        return status_list_tuple(constraint_status_list, conflict_status_list)

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
            refoppteam_cost = self.timebalancer.getSingleTeamELstats(div_id, refoppteam_id, 'early')
        elif refslot_index == lastTrueSlot:
            refoppteam_cost = self.timebalancer.getSingleTeamELstats(div_id,
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
                    refoppteam_swap_cost = self.timebalancer.getSingleTeamELstats(div_id, refoppteam_id, 'early')
                    if refoppteam_swap_cost >= swap_cost_threshold:
                        continue
                elif requireLate_flag and swap_slot_index == lastTrueSlot:
                    refoppteam_swap_cost = self.timebalancer.getSingleTeamELstats(div_id, refoppteam_id, 'late')
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
                swap_cost = self.timebalancer.getELcost_by_slot(swap_slot_index, swap_teams, lastTrueSlot)
                # ******** cost arithmetic using parameters
                if swap_cost > 0:
                    swap_cost = (swap_multweight*swap_cost) + swap_addweight
                # cost for swap teams to move into refslot (subtractive cost)
                swap_outgoing_cost = self.timebalancer.getELcost_by_slot(refslot_index, swap_teams, lastTrueSlot)
                # cost for ref teams to move into swapslot (subtractive)
                swap_incoming_cost = self.timebalancer.getELcost_by_slot(swap_slot_index, refteams, lastTrueSlot)
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

                self.timebalancer.updateSlotELCounters(refslot_index,
                    max_swap_slot_index, refteams, max_swap_teams, lastTrueSlot,
                    lastTrueSlot)
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
                'slotsperday':sstatus_len})
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
                required_slots += totalmatch['gameslots_perrnd_perdiv']*max(totalmatch['numgames_perteam_list'])
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
            else:
                # assuming previous tests passed, check if there are enough field
                # slots to accomodate number of games
                # NOTE 'available_slots' is an upper bound on availability as
                # gameslotsperday is defined for the field across all fielddays,
                # whereas in reality there may be limited availability days where
                # the number of slots may be less than the gameslotsperday value
                available_slots = sum(self.fieldstatus_list[self.fstatus_indexerGet(x)]['slotsperday']*self.fieldinfo_list[self.fieldinfo_indexerGet(x)]['totalfielddays'] for x in field_id_set)
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

    def init_homefieldweight_list(self):
        ''' This method creates two effective outputs, though the way we output
        (one as a return value and the other as assignment to a member variable)
        might not be the best of soft eng practices.
        First output (return value) is the aggregated home field weights for each
        field, aggregated over one division.
        Second output (assignemt to another key of self.tminfo) is the per-team
        field distribution weight 0.0-1.0 based on the af_list configuration.
        (If there is no af_list config, default to weight 1.0/divfields) The
        fractional per-field weights should sum to 1.0
        '''
        div_id_list = [x['div_id'] for x in self.divinfo_list]
        homefield_weight_list = list()
        for div_id in div_id_list:
            # iterate thorugh each
            if self.tminfo_indexerMatch:
                index_list = self.tminfo_indexerMatch(div_id)
            else:
                index_list = None
            divinfo = self.divinfo_list[self.divinfo_indexerGet(div_id)]
            divfield_list = divinfo['divfield_list']
            # see if there are any tminfo entries for the current div
            if index_list:
                # if there is at least one tminfo entry for the div, then
                # create the weight list for each field
                # weight list is defined as the aggregate, the sume of field weights
                # for team (tminfo entry)
                hfweight_list = list()
                for index in index_list:
                    # get indexer into current hfweight_list iteration
                    dindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(hfweight_list)).get(x)
                    af_list = self.tminfo_list[index]['af_list']
                    if not af_list:
                        # if there are no af_field field entries, default to full
                        # field list for the division (divfield)
                        af_list = divfield_list
                    # weight is a dilution factor when multple home fields are
                    # assigned to a team
                    weight = 1.0/len(af_list)
                    # save weight to tminfo_list; af_weight applies to each
                    # af_list entry
                    for af in af_list:
                        dindex = dindexerGet(af)
                        if dindex is not None:
                            hfweight_list[dindex]['aggregweight'] += weight
                        else:
                            hfweight_list.append({'field_id':af,
                                'aggregweight':weight})
                    # create list of effective weights for the current team_id
                    # if field is in af_list (affinity field list), then weight is
                    # inverset of number of fields in af_list, otherwise it is 0
                    effweight_list = [{'field_id':x, 'effweight':weight} if x in af_list else {'field_id':x, 'effweight':0.0} for x in divfield_list]
                    self.tminfo_list[index]['effweight_list'] = effweight_list
                # We will not be normalizing the weights as the absolute weight value
                # summed across all teams in the division will be necesary when
                # combining weights with another division
            else:
                # default to equal weights if the div has no tminfo config
                # create tminfo entry for effweight_list.  tminfo entries that
                # we are creating here will be fore memory only
                # dt_id, tm_id, div_id, af_list, along with effweight_list keys
                # will be created.  Will not be stored in db.
                effweight = 1.0/len(divfield_list)
                effweight_list = [{'field_id':x, 'effweight':effweight}
                    for x in divfield_list]
                totalteams = divinfo['totalteams']
                # create the default field distribution list to each team in div
                divtminfo_list = [{'div_id':div_id, 'tm_id':tm_id,
                    'dt_id':"dv"+str(div_id)+"tm"+str(tm_id),
                    'effweight_list':effweight_list, 'af_list':divfield_list[:]}
                    for tm_id in range(1, totalteams+1)]
                if not self.tminfo_list:
                    self.tminfo_list = divtminfo_list
                else:
                    self.tminfo_list.extend(divtminfo_list)
                aggregweight = float(totalteams)/len(divfield_list)
                hfweight_list = [{'field_id':x, 'aggregweight':aggregweight}
                    for x in divfield_list]
            homefield_weight_list.append({'div_id':div_id, 'hfweight_list':hfweight_list})
        if not self.tminfo_indexerGet:
            self.tminfo_indexerGet = lambda x: dict((p['dt_id'],i) for i,p in enumerate(self.tminfo_list)).get("dv"+str(x[0])+"tm"+str(x[1]))
            self.tminfo_indexerMatch = lambda x: [i for i,p in enumerate(self.tminfo_list) if p['div_id'] == x]
            self.fieldbalancer.tminfo_list = self.tminfo_list
            self.fieldbalancer.tminfo_indexerGet = self.tminfo_indexerGet
            self.fieldbalancer.tminfo_indexerMatch = self.tminfo_indexerMatch
        hf_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(homefield_weight_list)).get(x)
        return _List_Indexer(homefield_weight_list, hf_indexerGet)

    def get_aggregnorm_hfweight_list(self, connected_div_list):
        ''' Aggregate home field weight list based on divisions that make up the
        connected_div_list.  Simply sum over aggregweight values for each field.
        Go ahead and normalize the results also
        Note weight key is changed to normweight for a normalized dict entry'''
        norm_weight_list = list()
        sumweight = 0
        for div_id in connected_div_list:
            hfweight_list = self.homefield_weight_list[
                self.hfweight_indexerGet(div_id)]['hfweight_list']
            for hfweight in hfweight_list:
                aindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(norm_weight_list)).get(x)
                field_id = hfweight['field_id']
                aggregweight = hfweight['aggregweight']
                aindex = aindexerGet(field_id)
                if aindex is not None:
                    norm_weight_list[aindex]['normweight'] += aggregweight
                else:
                    norm_weight_list.append({'field_id':field_id,
                        'normweight':aggregweight})
                sumweight += aggregweight
        # calculate total weight across all fields so we can normalize
        for norm_weight in norm_weight_list:
            norm_weight['normweight'] /= sumweight
        nindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(norm_weight_list)).get(x)
        return _List_Indexer(norm_weight_list, nindexerGet)

    def calc_divreffield_distribution_list(self, ngperteam_list):
        ''' Determine division-wide target distribution of number of games for each
        field in the divlist for the whole season
        NOTE: do we need to extend expected field distribtuion to the
        connected div list level?  We will be extending the expected field
        distribution down to the team level below
        ngperteam_list includes numgames per team info for divs in the current
        connected_div_list'''
        targetfield_distribution_list = list()
        for ngperteam_dict in ngperteam_list:
            div_id = ngperteam_dict['div_id']
            # get total games for current division - sum games for each team, divide
            # by 2
            # Note - leave out the divide-by-2 factor now, as metrics we compare against are straight aggregation of matche counts which double counts
            # home and away team contributions
            div_totalgames = sum(ngperteam_dict['numgames_list'])
            hfweight_list = self.homefield_weight_list[self.hfweight_indexerGet(div_id)]['hfweight_list']
            # get inverse of sum - used for weight normalization
            inv_sumweight = 1.0/sum(x['aggregweight'] for x in hfweight_list)
            # get expected field distribution at the macro division usage level.
            # Multiply total number of games (per division) by normalized weight
            # of each field
            # x['aggregweight']*inv_sumweight is the fractional ration of total
            # games in div that should be hosted in field x
            distribution_list = [{'field_id':x['field_id'], 'sumcount':x['aggregweight']*inv_sumweight*div_totalgames} for x in hfweight_list]
            #target_list = [{'team_id':team_id, 'tmtarget_list':[{'field_id':y['field_id'], 'target':y['aggregweight']*inv_sumweight*numgames} for y in hfweight_list]} for team_id,numgames in enumerate(ngperteam_dict['numgames_list'], start=1)]
            targetfield_distribution_list.append({'div_id':div_id,
                'distrib_list':distribution_list})
        tindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(targetfield_distribution_list)).get(x)
        return _List_Indexer(targetfield_distribution_list, tindexerGet)
