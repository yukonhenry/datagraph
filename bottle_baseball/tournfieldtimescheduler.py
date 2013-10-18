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
from math import ceil
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_ScheduleParam = namedtuple('SchedParam', 'field_id gameday_id slot_index')
time_format_CONST = '%H:%M'
min_slotgap_CONST = 2
min_u10slotgap_CONST = 3
u10div_tuple = (100,200)

_absolute_earliest_time = parser.parse('05:00')
_min_timegap = timedelta(0,0,0,0,160) # in minutes

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
            max_slot_index = max(self.tfstatus_list[self.tfindexerGet(f)]['max_slot_index'] for f in field_list)

            endtime_list = [(f,parser.parse(self.tfieldinfo_list[self.tfindexerGet(f)]['end_time'])) for f in field_list]
            latest_endtime = max(endtime_list, key=itemgetter(1))[1]
            #field_cycle = cycle(fieldset)
            self.initTeamTimeGap_list(connected_div_list)
            if set(connected_div_list) == set(u10div_tuple):
                # if we are processing div U10, preallocate field time slots to each division (as they have different max rounds)
                self.reserveFieldTimeSlots(connected_div_list, field_list)
            current_gameday = 1
            #earliestfield_list = None
            for round_games in grouped_match_list:
                #current_gameday_list = [1,1]  # for U10
                #current_gameday = 1
                round_id = round_games['round_id']
                round_match_list = round_games['match_list']
                if round_id > 1:
                    self.optimizeMatchOrder(round_match_list)
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    #current_gameday_list = [1,1]  # for U10
                    #current_gameday = 1
                    #earliestfield_list = None
                    div_id = rrgame['div_id']
                    home = rrgame['home']
                    away = rrgame['away']
                    ginterval = self.divinfo_list[self.dindexerGet(div_id)]['gameinterval']
                    gameinterval = timedelta(0,0,0,0,ginterval)
                    search_tuple = self.getSearchStart_daytime(div_id, home, away, field_list, latest_endtime-gameinterval)
                    current_gameday = search_tuple[0]
                    current_start = search_tuple[1]
                    # start time calc needs to be done here as start times for fields may change based non gameday
                    starttime_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_gameday-1][0]['start_time']) for f in field_list]
                    found_tuple = self.findAlternateFieldSlot(field_list, current_gameday, current_start, starttime_list, endtime_list, gameinterval, div_id, home, away)
                    #earliest_dict = earliestfield_list.pop()
                    #efield = earliest_dict['field_id']
                    #eslot = earliest_dict['index']
                    efield = found_tuple.field_id
                    eslot = found_tuple.slot_index
                    egameday = found_tuple.gameday_id
                    selected_tfstatus = self.tfstatus_list[self.tfindexerGet(efield)]['slotstatus_list'][egameday-1][eslot]
                    logging.debug("tournftscheduler:generate:assignment success rrgame %s gameday %d field %d slot %d", rrgame, egameday, efield, eslot)
                    '''
                    validation_tuple = self.validateTimeSlot(div_id, efield, egameday, eslot, home, away)
                    if not validation_tuple[0]:
                        logging.debug("tournftscheduler:generate: validation failed div %d gameday %d eslot %d newgameday %d newslot %d field %d", div_id, current_gameday, eslot, validation_tuple[2], validation_tuple[1], efield)
                        alt_tuple = self.findAlternateFieldSlot(field_list, validation_tuple[2], validation_tuple[1], div_id, rrgame['home'], rrgame['away'])
                        if alt_tuple:
                            alt_field = alt_tuple.field_id
                            alt_gameday = alt_tuple.gameday_id
                            #current_gameday = alt_gameday
                            #if div_id in u10div_tuple:
                             #   current_gameday_list[div_id-1] = current_gameday
                            alt_slot = alt_tuple.slot_index
                            selected_tfstatus = self.tfstatus_list[self.tfindexerGet(alt_field)]['slotstatus_list'][alt_gameday-1][alt_slot]
                            revalidation_tuple = self.validateTimeSlot(div_id, alt_field, alt_gameday, alt_slot, rrgame['home'], rrgame['away'])
                            if not revalidation_tuple[0]:
                                raise CodeLogicError("tournftscheduler:generateSchedule: revalidation should have worked")
                            else:
                                logging.debug("tournftscheduler:generate:second revalidation success rrgame %s field %d slot %d", rrgame, alt_field, alt_slot)
                        else:
                            raise FieldAvailabilityError(div_id)
                    else:
                        selected_tfstatus = self.tfstatus_list[self.tfindexerGet(efield)]['slotstatus_list'][egameday-1][eslot]
                        logging.debug("tournftscheduler:generate:first revalidation success rrgame %s field %d slot %d", rrgame, efield, eslot)
                    '''
                    if selected_tfstatus['isgame']:
                        raise CodeLogicError("tournftscheduler:generate:game is already booked:")
                    selected_tfstatus['isgame'] = True
                    selected_tfstatus['teams'] = rrgame
                    self.updateTeamTimeGap_list(div_id, home, away, egameday, selected_tfstatus['start_time']+gameinterval)
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
            max_slot_index = len(sstatus_list)-1

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
                                            'slotstatus_list':slotstatus_list,
                                            'max_slot_index':max_slot_index,
                                            'end_time':end_time})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldseason_status_list)).get(x)
        return _List_Indexer(fieldseason_status_list, fstatus_indexerGet)

    def findNextEarliestFieldSlot(self, field_list, cur_gameday, div_id):
        cur_gameday_ind = cur_gameday-1
        status_list = [(f,
                        self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday_ind])
                        for f in field_list]
        if div_id in u10div_tuple:
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
        self.gaplist = [{'div_id':self.divinfo_list[self.dindexerGet(x)]['div_id'], 'team_id':y, 'last_end':-1, 'last_gameday':0} for x in div_list for y in range(1, self.divinfo_list[self.dindexerGet(x)]['totalteams']+1)]
        # gapindexerGet must have a (div_id, team_id) tuple passed to it
        self.gapindexerGet = lambda x: [i for i,p in enumerate(self.gaplist) if p['div_id'] == x[0] and p['team_id']==x[1]]

    def updateTeamTimeGap_list(self, div_id, home, away, gameday, end_time):
        for team in (home,away):
            gapindex_list = self.gapindexerGet((div_id, team))
            gapteam_dict = self.gaplist[gapindex_list[0]]
            gapteam_dict['last_end'] = end_time
            gapteam_dict['last_gameday'] = gameday

    def getSearchStart_daytime(self, div_id, home, away, field_list, latest_starttime):
        #minslot_gap = min_u10slotgap_CONST if div_id in (1,2) else min_slotgap_CONST
        homegap_dict = self.gaplist[self.gapindexerGet((div_id, home))[0]]
        awaygap_dict = self.gaplist[self.gapindexerGet((div_id, away))[0]]
        homegap_gameday = homegap_dict['last_gameday']
        awaygap_gameday = awaygap_dict['last_gameday']
        homegap_end = homegap_dict['last_end']
        awaygap_end = awaygap_dict['last_end']
        if homegap_gameday == awaygap_gameday:
            maxgap_gameday = homegap_gameday
            maxgap_end = max(homegap_end, awaygap_end)
        elif homegap_gameday > awaygap_gameday:
            maxgap_gameday = homegap_gameday
            maxgap_end = homegap_end
        else:
            maxgap_gameday = awaygap_gameday
            maxgap_end = awaygap_end
        if maxgap_gameday == 0 :
            next_gameday = 1
            next_start = _absolute_earliest_time
        else:
            next_gameday = maxgap_gameday
            if maxgap_end == -1:
                next_start == _absolute_earliest_time
            else:
                next_start = maxgap_end + _min_timegap
                if next_start > latest_starttime:
                    next_gameday += 1
                    next_start = _absolute_earliest_time
        #print 'homegap awaygap gameday slot', homegap_dict, awaygap_dict, next_gameday, next_end
        return (next_gameday, next_start)

    def validateTimeSlot(self, div_id, field_id, gameday, slot_index, home, away):
        # check if candidate time slot has enough gap with the previously assigned slot for the two teams in the match
        target_slot = 0 # default return value
        target_gameday = gameday
        min_slotgap = min_u10slotgap_CONST if div_id in (1,2) else min_slotgap_CONST
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
                #print 'FALSE div slot target gameday home away', div_id, slot_index, target_tuple[i], gameday, home, away
            if all(validate_flag):
                validate = True
                #print 'VALIDATE', div_id, home,away
                logging.debug("tournftscheduler:validateTimeSlot: validation Success slot=%d target gameday=%d",slot_index, gameday)
                for team in (home,away):
                    gapindex_list = self.gapindexerGet((div_id, team))
                    gapteam_dict = self.gaplist[gapindex_list[0]]
                    gapteam_dict['last_slot'] = slot_index
                    gapteam_dict['last_gameday'] = gameday
            else:
                validate = False
                max_slot_index = len(self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list'][gameday])
                target_slot = max(target_tuple)
                if target_slot > max_slot_index:
                    target_gameday = gameday + 1
                    target_slot = 0
                logging.debug("tournftscheduler:validateTimeSlot: validation failed new target slot=%d target gameday=%d",target_slot, target_gameday)
        return (validate, target_slot, target_gameday)

    def findAlternateFieldSlot(self, field_list, gameday, target_start, starttime_list, endtime_list, gameinterval, div_id, home, away):
        min_start = min(starttime_list, key=itemgetter(1))[1]
        max_end = max(endtime_list, key=itemgetter(1))[1]
        gameinterval_sec = gameinterval.total_seconds()
        gameday_ind = gameday-1
        max_slot_index = max(self.tfstatus_list[self.tfindexerGet(f)]['max_slot_index'] for f in field_list)
        slotstatus_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind]) for f in field_list]

        gamestart = min_start if target_start < min_start else target_start
        while gamestart + gameinterval <= max_end:
            s_set = set([s[0] for s in starttime_list if gamestart >= s[1]])
            e_set = set([e[0] for e in endtime_list if gamestart+gameinterval <= e[1]])
            f_list = list(s_set&e_set)
            limitedstatus_list = [s for s in slotstatus_list if s[0] in f_list]
            for limitedstatus in limitedstatus_list:
                #http://stackoverflow.com/questions/3694835/python-2-6-5-divide-timedelta-with-timedelta
                slot_index = int(ceil((gamestart - limitedstatus[1][0]['start_time']).total_seconds()/gameinterval_sec))
                if slot_index >= len(limitedstatus[1]):
                    continue
                if not limitedstatus[1][slot_index]['isgame']:
                    found_dict = {'field_id':limitedstatus[0],'slot_index':slot_index}
                    break
            else:
                gamestart += gameinterval
                continue
            break
            '''
            if status_list:
                status = status_list[0]
                logging.debug("tournftscheduler:findalt:alt found gameday=%d slot=%d", gameday, slot_index)
                #print 'alt field gameday target', status[0], gameday, target_slot
                break
            '''
        else:
            logging.debug("tournftscheduler:findaltfs:status_list is null gameday=%d target_start=%s div_id=%d home=%d away=%d",gameday, target_start, div_id, home, away)
            next_gameday = gameday + 1
            alt_list = None
            while True or next_gameday > 3:
                try:
                    alt_list = self.findNextEarliestFieldSlot(field_list, next_gameday, div_id)
                except ValueError:
                    logging.error("tournftscheduler:findalt: ValueError Exception div_id=%d, gameday=%d",div_id, next_gameday)
                    next_gameday += 1
                else:
                    if not alt_list:
                        logging.debug("tournftscheduler:generate:findalt returns div_id=%d, gameday=%d",div_id, next_gameday)
                        next_gameday += 1
                    else:
                        logging.debug("tournftscheduler:findalt: findNextEarliest found=%s", alt_list)
                        break
            else:
                logging.debug("tournftscheduler:findalt: findNextEarliest iteration, max gameday exceeded")
                return None
            if alt_list:
                alt_dict = alt_list[0]
                alt_field = alt_dict['field_id']
                alt_slot = alt_dict['index']
                return _ScheduleParam(alt_field, next_gameday, alt_slot)
            else:
                return None
        logging.debug("tournftscheduler:findalt: match slot found %s", found_dict)
        return _ScheduleParam(found_dict['field_id'], gameday, found_dict['slot_index'])

    def optimizeMatchOrder(self, rmlist):
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
                #cost = sum(10*self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_gameday'] + self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_end'] +1 for x in (home,away))
                cost = sum(10*self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_gameday'] for x in (home,away))
                for x in (home,away):
                    last_end = self.gaplist[self.gapindexerGet((div_id, x))[0]]['last_end']
                    if last_end != -1:
                    # note the difference against the earliest time or the division factor is not important - just needs to be consistent to calculate cost
                        cost += int(ceil((last_end - parser.parse('09:00')).total_seconds()/_min_timegap.total_seconds()))
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

