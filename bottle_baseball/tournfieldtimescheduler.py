''' Copyright YukonTR 2013 '''

from schedule_util import getConnectedDivisionGroup
from itertools import groupby, cycle
from operator import itemgetter
from schedule_util import roundrobin
from datetime import timedelta
from dateutil import parser
from copy import deepcopy
from collections import namedtuple
from leaguedivprep import getTournAgeGenderDivision
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, CodeLogicError, SchedulerConfigurationError
import logging
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_ScheduleParam = namedtuple('SchedParam', 'field_id gameday_id slot_index')
time_format_CONST = '%H:%M'
min_slotgap_CONST = 2
min_u10slotgap_CONST = 3

class TournamentFieldTimeScheduler:
    def __init__(self, tdbinterface, tfield_tuple, divinfo, dindexerGet):
        self.tdbInterface = tdbinterface
        self.tfieldinfo_list = tfield_tuple.dict_list
        self.tfindexerGet = tfield_tuple.indexerGet
        self.connected_div_components = getConnectedDivisionGroup(self.tfieldinfo_list)
        self.divinfo_list = divinfo
        self.dindexerGet = dindexerGet
        tfstatus_tuple = self.getTournFieldSeasonStatus_list()
        self.tfstatus_list = tfstatus_tuple.dict_list
        self.tfindexerGet = tfstatus_tuple.indexerGet
        self.gaplist = None
        self.gapindexerGet = None
        # add field parameters to the divinfo list entries
        # better to eventually move this to the tournamentscheduler constructor
        for tfield in self.tfieldinfo_list:
            f_id = tfield['field_id']
            for d_id in tfield['primary']:
                index = self.dindexerGet(d_id)
                if index is not None:
                    division = self.divinfo_list[index]
                    # check existence of key 'fields' - if it exists, append to list of fields, if not create
                    if 'fields' in division:
                        division['fields'].append(f_id)
                    else:
                        division['fields'] = [f_id]

    def generateSchedule(self, totalmatch_list):
        tmindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.tdbInterface.dbInterface.dropGameDocuments()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            # flatten out the list embed div_id value in each dictionary
            # also flatten out 'GAME_TEAM' list generate by the match generator
            flatmatch_list = [{'ROUND_ID':z['ROUND_ID'], 'HOME':p['HOME'], 'AWAY':p['AWAY'], 'DIV_ID':x['div_id']} for x in connecteddiv_match_list for y in x['match_list'] for z in y for p in z['GAME_TEAM']]
            # sort the list according to round_id (needed for groupby below), and then by div_id
            sorted_flatmatch_list = sorted(flatmatch_list, key=itemgetter('ROUND_ID', 'DIV_ID'))
            # group list by round_id; dict value of 'match_list' key is a nested array, which sis created by an inner groupby based on div_id
            # The nested list will be passed to the roundrobin multiplexer
            #for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID')):
            #   for key1, items1 in groupby(items, key=itemgetter('DIV_ID')):
            #      for j in items1:
            #         print key, key1, j
            grouped_match_list = [{'round_id':rkey, 'match_list':[[{'home':x['HOME'], 'away':x['AWAY'], 'div_id':dkey} for x in ditems] for dkey, ditems in groupby(ritems, key=itemgetter('DIV_ID'))]} for rkey, ritems in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            logging.debug("tournftscheduler:gensched:groupedlist=%s", grouped_match_list)
            #find the fields available for the connected_div_set by finding
            # the union of fields for each div
            # another option is to  call set.update (see fieldtimeschedule fset)
            fieldset = reduce(set.union,
                              map(set,[self.divinfo_list[self.dindexerGet(x)]['fields'] for x in connected_div_list]))
            field_list = list(fieldset)
            #field_cycle = cycle(fieldset)
            self.initTeamTimeGap_list(connected_div_list)
            if set(connected_div_list) == set([1,2]):
                # if we are processing div U10, preallocate field time slots to each division (as they have different max rounds)
                self.reserveFieldTimeSlots(connected_div_list, field_list)
#                for field in field_list:
#                    print 'field tfstatus', field, self.tfstatus_list[self.tfindexerGet(field)]
            current_gameday_list = [1,1]  # for U10
            current_gameday = 1
            earliestfield_list = None
            for round_games in grouped_match_list:
                current_gameday_list = [1,1]  # for U10
                current_gameday = 1
                round_id = round_games['round_id']
                #current_gameday = (round_id-1)/2 + 1
                round_match_list = round_games['match_list']
                if round_id > 1:
                    self.optimizeMatchOrder(round_match_list, current_gameday)
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    current_gameday_list = [1,1]  # for U10
                    current_gameday = 1
                    earliestfield_list = None
                    div_id = rrgame['div_id']
                    if div_id in (1,2):
                        current_gameday = current_gameday_list[div_id-1]
                    if not earliestfield_list:
                        accept_flag = False
                        while True or current_gameday > 3:
                            try:
                                earliestfield_list = self.findNextEarliestFieldSlot(field_list, current_gameday, div_id)
                            except ValueError:
                                current_gameday += 1
                            else:
                                if not earliestfield_list:
                                    current_gameday += 1
                                else:
                                    break
                        if div_id in (1,2):
                            current_gameday_list[div_id-1] = current_gameday
                    earliest_dict = earliestfield_list.pop()
                    efield = earliest_dict['field_id']
                    eslot = earliest_dict['index']
                    validation_tuple = self.validateTimeSlot(div_id, current_gameday, eslot, rrgame['home'], rrgame['away'])
                    if not validation_tuple[0]:
                        alt_tuple = self.findAlternateFieldSlot(field_list, current_gameday, validation_tuple[1], div_id, rrgame['home'], rrgame['away'])
                        if alt_tuple:
                            alt_field = alt_tuple.field_id
                            alt_gameday = alt_tuple.gameday_id
                            #current_gameday = alt_gameday
                            #if div_id in (1,2):
                             #   current_gameday_list[div_id-1] = current_gameday
                            alt_slot = alt_tuple.slot_index
                            selected_tfstatus = self.tfstatus_list[self.tfindexerGet(alt_field)]['slotstatus_list'][alt_gameday-1][alt_slot]
                            revalidation_tuple = self.validateTimeSlot(div_id, alt_gameday, alt_slot, rrgame['home'], rrgame['away'])
                            if not revalidation_tuple[0]:
                                raise CodeLogicError("tournftscheduler:generateSchedule: revalidation should have worked")
                        else:
                            raise FieldAvailabilityError(div_id)
                    else:
                        selected_tfstatus = self.tfstatus_list[self.tfindexerGet(efield)]['slotstatus_list'][current_gameday-1][eslot]
                    selected_tfstatus['isgame'] = True
                    selected_tfstatus['teams'] = rrgame
            for field_id in fieldset:
                gameday_id = 1
                for gameday_list in self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list']:
                    if gameday_list:
                        for match in gameday_list:
                            if match['isgame']:
                                gametime = match['start_time']
                                teams = match['teams']
                                div_id = teams['div_id']
                                home_id = teams['home']
                                away_id = teams['away']
                                div = getTournAgeGenderDivision(div_id)
                                print div.age, div.gender, gameday_id, field_id, home_id, away_id, teams, gametime
                                self.tdbInterface.dbInterface.insertGameData(div.age, div.gender, gameday_id, gametime.strftime(time_format_CONST), field_id, home_id, away_id)
                    gameday_id += 1
        self.tdbInterface.dbInterface.setSchedStatus_col()

    def getTournFieldSeasonStatus_list(self):
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldseason_status_list = []
        for f in self.tfieldinfo_list:
            f_id = f['field_id']
            numgamedays = f['numgamedays']
            gamestart = parser.parse(f['start_time'])
            end_time = parser.parse(f['end_time'])
            # take max for now - this is a simplification
            # default for phmsa is that divisions that share a field have
            # same game intervals
            ginterval = max(self.divinfo_list[self.dindexerGet(p)]['gameinterval'] for p in f['primary'])
            # convert to datetime compatible obj
            gameinterval = timedelta(0,0,0,0,ginterval)
            # slotstatus_list has a list of statuses, one for each gameslot
            # create game status list for default start/end time days
            sstatus_list = []
            while gamestart + gameinterval <= end_time:
                # for above, correct statement should be adding pure gametime only
                sstatus_list.append({'start_time':gamestart, 'isgame':False})
                gamestart += gameinterval

            # find gamedays with different field availability times
            ldays_list = f.get('limiteddays')
            lallstatus_list = []
            if ldays_list:
                for lday in ldays_list:
                    lgameday = lday['gameday']
                    lgamestart = parser.parse(lday['start_time'])
                    lgameend = parser.parse(lday['end_time'])
                    lstatus_list = []
                    while lgamestart + gameinterval <= lgameend:
                        lstatus_list.append({'start_time':lgamestart,
                                            'isgame':False})
                        lgamestart += gameinterval
                    lallstatus_list.append({'lgameday':lgameday,
                                           'lstatus_list':lstatus_list})
                lindexerGet = lambda x: dict((p['lgameday'],i) for i,p in enumerate(lallstatus_list)).get(x)

            # find gamedays w closed field
            closed_list = f.get('closed_gameday_list')
            # assign appropriate slotsstatus list for each gameday
            # for current field_id
            slotstatus_list = numgamedays*[None] #initialize
            for gameday in range(1,numgamedays+1):
                if closed_list and gameday in closed_list:
                    # leave slotstatus_list entry as None
                    continue
                elif lallstatus_list and lindexerGet(gameday) is not None:
                    lindex = lindexerGet(gameday)
                    # decrement index by one from gameday value as gameday is
                    # 1-indexed
                    slotstatus_list[gameday-1] = lallstatus_list[lindex]['lstatus_list']
                else:
                    slotstatus_list[gameday-1] = deepcopy(sstatus_list)

            fieldseason_status_list.append({'field_id':f['field_id'],
                                            'slotstatus_list':slotstatus_list})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldseason_status_list)).get(x)
        return _List_Indexer(fieldseason_status_list, fstatus_indexerGet)

    def findNextEarliestFieldSlot(self, field_list, cur_gameday, div_id):
        print 'gameday', cur_gameday
        cur_gameday_ind = cur_gameday-1
        field_cycle = cycle(field_list)
        status_list = [(f,
                        self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday_ind])
                        for f in field_list]
        if div_id in (1,2):
            allindex_list = [(s[0],[i for i,j in enumerate(s[1]) if not j['isgame'] and j['div_id']==div_id]) for s in status_list if not all(x['isgame'] for x in s[1])]
            if not allindex_list:
                return None
            try:
                firstindex_list = [(x[0],min(x[1])) for x in allindex_list]
            except ValueError:
                raise ValueError
            print 'firstind for U10', div_id, allindex_list, firstindex_list
        else:
            firstindex_list = [(s[0],[x['isgame'] for x in s[1]].index(False))
                                for s in status_list if not all(x['isgame'] for x in s[1])]
        if not firstindex_list:
            return None
        #print 'firstindex', firstindex_list
        mintime = min(firstindex_list, key=itemgetter(1))
        #print 'mintime', mintime
        mintime_list = [{'field_id':f[0], 'index':f[1]} for f in firstindex_list if f[1] == min(firstindex_list, key=itemgetter(1))[1]]
        #print 'mintime_list', mintime_list
        return mintime_list

    def initTeamTimeGap_list(self, div_list):
        self.gaplist = [{'div_id':self.divinfo_list[self.dindexerGet(x)]['div_id'], 'team_id':y, 'last_slot':-1, 'last_gameday':0} for x in div_list for y in range(1, self.divinfo_list[self.dindexerGet(x)]['totalteams']+1)]
        # gapindexerGet must have a (div_id, team_id) tuple passed to it
        self.gapindexerGet = lambda x: [i for i,p in enumerate(self.gaplist) if p['div_id'] == x[0] and p['team_id']==x[1]]

    def validateTimeSlot(self, div_id, gameday, slot_index, home, away):
        # check if candidate time slot has enough gap with the previously assigned slot for the two teams in the match
        target_slot = 0 # default return value
        min_slotgap = min_u10slotgap_CONST if div_id in [1,2] else min_slotgap_CONST
        validate_flag = [False, False]
        target_tuple =  [-1,-1]
        for i, team in enumerate((home,away)):
            gapindex_list = self.gapindexerGet((div_id, team))
            if len(gapindex_list) != 1:
                raise CodeLogicError("tournftscheduler:initteamtimegap:gap list has multiple or No entries for div %d team %d indexlist %s" % (div_id, team, gapindex_list))
            gapteam_dict = self.gaplist[gapindex_list[0]]
            gapslot = gapteam_dict['last_slot']
            gapday = gapteam_dict['last_gameday']
            #print 'div team home away gapslot gapday slot_index gameday',div_id, team, home, away, gapslot, gapday, slot_index, gameday
            if (gapslot == -1 and gapday == 0):
                validate_flag[i] = True
            elif (gameday > gapday):
                validate_flag[i] = True
            elif (gapday == gameday and slot_index-gapslot > min_slotgap):
                validate_flag[i] = True
            else:
                #print 'slot gapslot', slot_index, gapslot
                validate_flag[i] = False
                logging.info("tourn_ftscheduler:validatetimeslot: TimeGap Validation Failed, div_id=%d slot_index=%d gameday=%d home=%d away=%d",
                             div_id, slot_index, gameday, home, away)
                # target slot is the minimu slot that gives the required game gap
                target_tuple[i] = gapslot + min_slotgap + 1
                print 'FALSE div slot target gameday home away', div_id, slot_index, target_tuple[i], gameday, home, away
            if all(validate_flag):
                validate = True
                #print 'VALIDATE', div_id, home,away
                for team in (home,away):
                    gapindex_list = self.gapindexerGet((div_id, team))
                    gapteam_dict = self.gaplist[gapindex_list[0]]
                    gapteam_dict['last_slot'] = slot_index
                    gapteam_dict['last_gameday'] = gameday
            else:
                validate = False
                target_slot = max(target_tuple)

        return (validate, target_slot)

    def findAlternateFieldSlot(self, field_list, gameday, target_slot, div_id, home, away):
        gameday_ind = gameday-1
        if div_id in (1,2):
            status_list = [(f,
                            self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot])
                            for f in field_list if len(self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind]) > target_slot and not self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot]['isgame'] and self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot]['div_id']==div_id]
        else:
            status_list = [(f,
                            self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot])
                            for f in field_list if len(self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind]) > target_slot and not self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot]['isgame']]
        #print 'status gameday target div home away', status_list, gameday, target_slot, div_id, home, away
        if status_list:
            status = status_list[0]
            print 'alt field gameday target', status[0], gameday, target_slot
            return _ScheduleParam(status[0], gameday, target_slot)
        else:
            next_gameday = gameday + 1
            try:
                alt_list = self.findNextEarliestFieldSlot(field_list, next_gameday, div_id)
            except ValueError:
                next_gameday += 1
                alt_list = self.findNextEarliestFieldSlot(field_list, next_gameday, div_id)
            if alt_list:
                alt_dict = alt_list[0]
                alt_field = alt_dict['field_id']
                alt_slot = alt_dict['index']
                return _ScheduleParam(alt_field, next_gameday, alt_slot)
            else:
                return None

    def optimizeMatchOrder(self, rmlist, gameday):
        #print 'gameday', gameday
        for divmatch_list in rmlist:
            #print 'divmatch', divmatch_list
            for match in divmatch_list:
                div_id = match['div_id']
                home = match['home']
                away = match['away']
                #*********************#
                # cost calculation for ordering of matches
                # low cost if match has been scheduled earlier - cost is
                # sum of cost for home and away games.  gameday multiplied by 10
                # and added to slot number + 1 (because default slot is -1)
                cost = sum(10*self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_gameday'] + self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_slot'] +1 for x in (home,away))
                match['cost'] = cost
                #print 'cost match home away', cost, match, self.gaplist[self.gapindexerGet((div_id, home))[0]], self.gaplist[self.gapindexerGet((div_id, away))[0]]
            divmatch_list.sort(key=itemgetter('cost'))
            #print 'divmatch after sort', divmatch_list

    def reserveFieldTimeSlots(self, connected_div_list, field_list):
        max_rr_gamedays = max(self.divinfo_list[self.dindexerGet(div)]['rr_gamedays'] for div in connected_div_list)

        total_gameday_slots = sum(len(self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][0]) for f in field_list)
        # total slots that we are going to reserve for a div over max_rrgamedays
        total_slots = total_gameday_slots * (max_rr_gamedays+2)
        #print 'reserving rrgame totalgame total', max_rr_gamedays, total_gameday_slots, total_slots
        total_fields = len(field_list)
        print 'max_rr totalslots totalfields', max_rr_gamedays, total_slots, total_fields
        fstatus_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list']) for f in field_list]
        #print 'fstatus_list', fstatus_list
        fstatus_list_cycle = cycle(fstatus_list)
        div_id_cycle = cycle(connected_div_list)
        for slot_count in range(total_slots):
            fstatus = fstatus_list_cycle.next()
            div_id = div_id_cycle.next()
            # gameday_ind is an INDEX and not an ID
            gameday_ind = slot_count / total_gameday_slots
            slot_index = slot_count % total_gameday_slots / total_fields
            fstatus[1][gameday_ind][slot_index]['div_id'] = div_id

#        for fstatus in fstatus_list:
#           print 'field fstatus', fstatus[0], fstatus[1]
        '''
        for div_id in connected_div_list:
            reserve_days = self.divinfo_list[self.dindexerGet(div_id)]['rr_gamedays']
            #for f in field_list:
            #    self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind][target_slot]

            fstatus_list = [(f, self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list']) for f in field_list]
            fstatus_cycle = cycle(fstatus_list)
            for gameday_ind in range(reserve_days):
        '''

