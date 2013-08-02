from datetime import  datetime, timedelta
from itertools import cycle
from schedule_util import roundrobin, all_same, all_value, enum, shift_list
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision, getFieldSeasonStatus_list, getDivFieldEdgeWeight_list, \
     getConnectedDivisions, getLeagueDivInfo, getFieldInfo
import logging
from operator import itemgetter
from copy import deepcopy
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError
from math import ceil, floor
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
        for gd in gd_fieldcount:
            diff = gd['count'] - requiredslots_perfield
            if diff >= 0:
                # 1 is a slack term, arbitrary
                maxedout_field = gd['field_id']
                penalty = (diff + 1)*2
            elif diff >= -2:
                almostmaxed_field = gd['field_id']
                if diff == -2:
                    penalty = 1  # give small additive penalty
                else:
                    # it can only be -1 here based on above logic
                    penalty = 2
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

    def ReFieldBalance(self, connected_div_list, fieldmetrics_list, indexerGet):
        rebalance_count = 0
        for div_id in connected_div_list:
            tfmetrics = fieldmetrics_list[indexerGet(div_id)]['tfmetrics']
            team_id = 1
            for team_metrics in tfmetrics:
                maxuse = max(team_metrics, key=itemgetter('count'))
                minuse = min(team_metrics, key=itemgetter('count'))
                if maxuse['count']-minuse['count'] > 1:
                    print div_id, team_id, 'needs to move from field', maxuse['field_id'], 'to', minuse['field_id']
                team_id += 1

    def generateSchedule(self, total_match_list):
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in total_match_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        # indexer below is used to protect against list of dictionaries that are not ordered according to id,
        # though it is a protective measure, as the list should be ordered with the id.
        match_list_indexer = dict((p['div_id'],i) for i,p in enumerate(total_match_list))
        self.dbinterface.dropGameCollection()  # reset game schedule collection

        # used for calaculating time balancing metrics
        ew_list_indexer = getDivFieldEdgeWeight_list()
        #enum defined in sched_util.py
        EL_enum = enum(NORMAL=0x0, EARLY_DIVTOTAL=0x1, LATE_DIVTOTAL=0x2, EARLY_TEAM=0x4, LATE_TEAM=0x8)

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
                numgameslots = divinfo['gamesperseason']
                # expected total fair share of number of early OR late games for each division
                # eff_edgeweight represents 'fair share' of fields
                # factor of 2 comes in because each time slots gets credited to two teams
                # (home and away)
                ew_list = ew_list_indexer.dict_list
                ew_indexerGet = ew_list_indexer.indexerGet
                divtarget_el = 2*numgameslots*ew_list[ew_indexerGet(div_id)]['ratio']
                # per team fair share of early or late time slots
                teamtarget_el = int(ceil(divtarget_el/numteams))  # float value
                # calculate each team's target share of early and late games
                earlylate_list = [{'early':teamtarget_el, 'late':teamtarget_el} for i in range(numteams)]
                self.target_earlylate_list.append({'div_id':div_id, 'target_list':earlylate_list})
                # each division's target share of early and late games
                # we have this metric because we are using 'ceil' for the team target so not every team
                # will have to meet requirements
                divtotal_el_list.append({'div_id':div_id, 'early':int(floor(divtarget_el)),
                                                'late':int(floor(divtarget_el))})
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
            cel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.current_earlylate_list)).get(x)
            tel_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(self.target_earlylate_list)).get(x)

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

                    tel_index = tel_indexerGet(div_id)
                    target_el_list = self.target_earlylate_list[tel_index]['target_list']
                    home_targetel_dict = target_el_list[home_id-1]
                    away_targetel_dict = target_el_list[away_id-1]
                    cel_index = cel_indexerGet(div_id)
                    current_el_list = self.current_earlylate_list[cel_index]['counter_list']
                    home_currentel_dict = current_el_list[home_id-1]
                    away_currentel_dict = current_el_list[away_id-1]

                    divtotal_el_dict = divtotal_el_list[divtotalel_indexer.get(div_id)]
                    divearly_count = sum(current_el_list[x]['early'] for x in range(len(current_el_list)))
                    divlate_count = sum(current_el_list[x]['late'] for x in range(len(current_el_list)))
                    el_state = EL_enum.NORMAL
                    if (divearly_count < divtotal_el_dict['early']):
                        el_state |= EL_enum.EARLY_DIVTOTAL
                    if (divlate_count < divtotal_el_dict['late']):
                        el_state |= EL_enum.LATE_DIVTOTAL
                    if (home_currentel_dict['early'] < home_targetel_dict['early'] and
                        away_currentel_dict['early'] < away_targetel_dict['early']):
                        el_state |= EL_enum.EARLY_TEAM
                    if (home_currentel_dict['late'] < home_targetel_dict['late'] and
                          away_currentel_dict['late'] < away_targetel_dict['late']):
                        el_state |= EL_enum.LATE_TEAM

                    logging.debug("----------------------")
                    logging.debug("fieldtimescheduler: rrgenobj loop div=%d round_id=%d home=%d away=%d",
                                  div_id, round_id, home_id, away_id)
                    logging.debug("early late hometarget=%s awaytarget=%s homecurrent=%s awaycurrent=%s",
                                  home_targetel_dict, away_targetel_dict, home_currentel_dict, away_currentel_dict)
                    submin = 0
                    while True:
                        fieldcand_list = self.findMinimumCountField(home_fieldmetrics_list, away_fieldmetrics_list,
                                                                    gameday_fieldcount, required_gameslotsperday, submin)
                        if fieldcand_list is None:
                            raise FieldAvailabilityError(div_id)
                        logging.debug("rrgenobj while True loop:")
                        logging.debug("divid=%d round_id=%d home=%d away=%d homemetrics=%s awaymetrics=%s mincount fields=%s",
                                      div_id, round_id, home_id, away_id, home_fieldmetrics_list, away_fieldmetrics_list, fieldcand_list)
                        logging.debug("fieldcandlist=%s",fieldcand_list)
                        if len(fieldcand_list) > 1:
                            isgame_list = [(x,
                                            [y['isgame'] for y in self.fieldSeasonStatus[self.fstatus_indexerGet(x)]
                                             ['slotstatus_list'][round_id-1]])
                                           for x in fieldcand_list]
                            if el_state & EL_enum.LATE_TEAM and el_state & EL_enum.LATE_DIVTOTAL:
                                # only look for last element, if el_state dictates so; if div totals are already met, skip
                                # if we are looking for last time slot, first get a list for available last time slot
                                # across all fields
                                lastslot_list = [(x[0],len(x[1])-1) for x in isgame_list if x[1][-1] is False]
                                if not all_value(lastslot_list, None):
                                    # if there is at least one open last time slot
                                    field_id = lastslot_list[0][0]
                                    slot_index = lastslot_list[0][1]
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    break
                            # ref http://stackoverflow.com/questions/3989016/how-to-find-positions-of-the-list-maximum
                            # for finding all indices with 'False' status (note we are not trying to find max here as the ref)
                            openslot_list = [(x[0],[i for i,j in enumerate(x[1]) if j==False])
                                             for x in isgame_list if not all_value(x[1],True)]
                            # first get the list of field/status dictionaries before searching for the False field
                            if all_value(openslot_list, None):
                                logging.info("fieldtimescheduler: fields %s are full",[x[0] for x in isgame_list])
                                submin += 1
                                continue
                            while openslot_list:
                                # loop the openslot (timeslot) list until a timeslot has been picked
                                # for everyloop, candidate timeslots may be decreased based on earlylate status
                                # Loop will break if a timeslot has been discovered.
                                earliestslot_list = [(x[0],min(x[1])) for x in openslot_list]
                                # find min of open timeslots
                                # http://docs.python.org/2/howto/sorting.html
                                # sort based on first index of isgame 'False' which maps to earliest time
                                # game that needs to be filled amongst available fields
                                sorted_earliestslot_list = sorted(earliestslot_list, key=itemgetter(1))
                                logging.debug("ftscheduler:while openslotlist=%s: div=%d, earliestslot=%s sorted=%s",
                                              openslot_list, div_id, earliestslot_list, sorted_earliestslot_list)
                                if (all_value([len(x[1]) for x in openslot_list], 1) and
                                    all_value([x[1] for x in sorted_earliestslot_list], 0)):
                                    field_id = sorted_earliestslot_list[0][0]
                                    slot_index = sorted_earliestslot_list[0][1]
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    logging.debug("ftscheduler:while openslot, default to 0 index because it is only choice")
                                    break  # from openslot_list
                                #loop through the sorted list - only time we don't break is
                                #when slot_index is 0 but that el_state is not EARLY
                                for el in sorted_earliestslot_list:
                                    field_id = el[0]
                                    slot_index = el[1]
                                    if slot_index == 0:
                                        if el_state & EL_enum.EARLY_TEAM and el_state & EL_enum.EARLY_DIVTOTAL:
                                            # if div totals are already met (EARLY_DIVTOTAL bit will be off), ok to assign
                                            # slot 0 even if EL_enum.EARLY has not been satisfied
                                            self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                            break # break out of for loop
                                        else:
                                            continue #continue for loop
                                    else:
                                        break # break out of for loop
                                else:
                                    # we want to save index0 (earlies time slot) for other games
                                    # remake openslot_list by deleting elements that we have already tested with
                                    # earliestslot_list (or its sorted version)
                                    # and then continue to beginning of while loop
                                    # we should only go through this once
                                    logging.debug("$$$$$$$$$$$$$$$$")
                                    logging.debug("ftscheduler:while openslotlist for else removing from %s",
                                                  openslot_list)
                                    openslot_indexer =  dict((p[0],i) for i,p in enumerate(openslot_list))
                                    for sel in sorted_earliestslot_list:
                                        sind = openslot_indexer.get(sel[0])
                                        logging.debug("ftscheduler:while openslot for sel=%s ind=%d",sel, sind)
                                        openslot_list[sind][1].remove(sel[1])
                                        if not openslot_list[sind][1]:
                                            logging.debug("ftscheduler:while openslotlist for else remove index %d",
                                                          sind)
                                            del openslot_list[sind]
                                            # important to re-define indexer because we deleted one index
                                            openslot_indexer =  dict((p[0],i) for i,p in enumerate(openslot_list))


                                    logging.info("^^^^^^^^^^^^^^^^^^^^")
                                    logging.info("ftscheduler: while openslolist: removed %s from openslot list, new list= %s",
                                                 sorted_earliestslot_list, openslot_list)
                                    continue
                                logging.info("ftscheduler: >1 fieldcandlist elstate=%d  fieldid=%d timeslot=%d selected",
                                             el_state, field_id, slot_index)
                                break # break out of while openslot_list
                            else:
                                logging.debug("ftscheduler: !!!!!!!!!!!!!!!!!!")
                                logging.debug("ftscheduler: openslot_list exhausted, should have just assigned slot 0")
                                raise TimeSlotAvailabilityError(div_id)
                            break # break out of while True
                        else:
                            field_id = fieldcand_list[0]
                            fsindex = self.fstatus_indexerGet(field_id)
                            # find status list for this round
                            fieldslotstatus_list = self.fieldSeasonStatus[fsindex]['slotstatus_list'][round_id-1]
                            # find first open time slot in round
                            isgame_list = [y['isgame'] for y in fieldslotstatus_list]
                            if el_state & EL_enum.LATE_TEAM and el_state & EL_enum.LATE_DIVTOTAL:
                                lastslot_state = isgame_list[-1]
                                if lastslot_state is False:
                                    slot_index = len(isgame_list)-1
                                    self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'late')
                                    break # out of while true
                            if not all_value(isgame_list, True):
                                openslotone_list = [i for i,j in enumerate(isgame_list) if not j]
                                slot_index = openslotone_list[0]
                                if slot_index == 0:
                                    if ((el_state & EL_enum.EARLY_TEAM and el_state & EL_enum.EARLY_DIVTOTAL) or
                                        len(openslotone_list)==1):
                                        self.incrementEL_counters(home_currentel_dict, away_currentel_dict, 'early')
                                    else:
                                        slot_index = openslotone_list[1]
                                break # out of while True
                            else:
                                submin += 1
                                logging.info("fieldtimescheduler: current minimum count field is all filled, try another %d",
                                             submin)
                                continue # w. while True

                    # these get exected after while True breaks
                    logging.debug("ftscheduler: after timeslot assign div=%d round_id=%d home_id=%d away_id=%d",
                                  div_id, round_id, home_id, away_id)
                    logging.debug("ftscheduler: slotind=%d home_currentel=%s away_currentel=%s",
                                  slot_index, home_currentel_dict, away_currentel_dict)
                    selected_ftstatus = self.fieldSeasonStatus[self.fstatus_indexerGet(field_id)]['slotstatus_list'][round_id-1][slot_index]
                    selected_ftstatus['isgame'] = True
                    gametime = selected_ftstatus['start_time']
                    home_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list))
                    away_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list))
                    home_fieldmetrics_list[home_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    away_fieldmetrics_list[away_fieldmetrics_indexer.get(field_id)]['count'] += 1

                    gameday_fieldcount[gd_fieldcount_indexerGet(field_id)]['count'] += 1
                    div = getAgeGenderDivision(div_id)
                    logging.debug("div=%s%s round_id=%d, field=%d gametime=%s slotindex=%d",
                                  div.age, div.gender, round_id, field_id, gametime, slot_index)
                    self.dbinterface.insertGameData(div.age, div.gender, rrgame['round_id'],
                                                    gametime.strftime(time_format_CONST),
                                                    field_id, home_id, away_id)
                logging.debug("ftscheduler: divlist=%s end of round=%d gameday_fieldcount=%s",
                              connected_div_list, round_id, gameday_fieldcount)
            rebalance_count = self.ReFieldBalance(connected_div_list, fieldmetrics_list, fieldmetrics_indexerGet)

        # executes after entire schedule for all divisions is generated
        self.compactTimeSchedule()
        divlist = [x['div_id'] for x in self.leaguediv]
        divlist.sort()  # note assignment b=a.sort() returns None
        for div_id in divlist:
            celdiv_list = self.current_earlylate_list[cel_indexerGet(div_id)]['counter_list']
            celearly_list = [x['early'] for x in celdiv_list]
            cellate_list = [x['late'] for x in celdiv_list]
            teldiv_list = self.target_earlylate_list[tel_indexerGet(div_id)]['target_list']
            #print div_id, celearly_list, cellate_list, teldiv_list


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
