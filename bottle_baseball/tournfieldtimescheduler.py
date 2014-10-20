''' Copyright YukonTR 2013 '''

from schedule_util import getConnectedDivisionGroup
from itertools import groupby, cycle
from operator import itemgetter
from schedule_util import roundrobin
from datetime import timedelta
from dateutil import parser
from copy import deepcopy
from collections import namedtuple
from sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, CodeLogicError, SchedulerConfigurationError
import logging
from math import ceil
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_ScheduleParam = namedtuple('SchedParam', 'field_id fieldday_id slot_index')
time_format_CONST = '%H:%M'
min_slotgap_CONST = 2
min_u10slotgap_CONST = 3
u10div_tuple = (100,200)
IDPROPERTY_str = 'tourndiv_id'
GAME_TEAM_str = 'game_team'
_absolute_earliest_time = parser.parse('05:00').time()
_absolute_earliest_date = parser.parse('01/01/2010').date()
_absolute_earliest_time = parser.parse('05:00')
_min_timegap = timedelta(0,0,0,0,160) # in minutes

class TournamentFieldTimeScheduleGenerator:
    def __init__(self, dbinterface, fieldinfo_tuple, divinfo_tuple):
        self.dbinterface = dbinterface
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.connected_div_components = getConnectedDivisionGroup(self.fieldinfo_list)
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        #tfstatus_tuple = self.getTournFieldSeasonStatus_list()
        fstatus_tuple = self.getFieldSeasonStatus_list()
        self.tfstatus_list = fstatus_tuple.dict_list
        self.tfindexerGet = fstatus_tuple.indexerGet
        self.timegap_list = None
        self.timegap_indexerGet = None
        # add field parameters to the divinfo list entries
        # better to eventually move this to the tournamentscheduler constructor
        for tfield in self.fieldinfo_list:
            f_id = tfield['field_id']
            for d_id in tfield['primaryuse_list']:
                index = self.dindexerGet(d_id)
                if index is not None:
                    division = self.divinfo_list[index]
                    # check existence of key 'divfield_list' - if it exists, append to list of fields, if not create
                    if 'divfield_list' in division:
                        division['divfield_list'].append(f_id)
                    else:
                        division['divfield_list'] = [f_id]

    def mapdatetime_fieldday(self, field_id, dt_obj, key):
        ''' Map datetime date to fieldday_id as defined by the calendarmap_list
        for the field_id '''
        fieldinfo_list = self.fieldinfo_list[self.findexerGet(field_id)]
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
        fieldinfo_list = self.fieldinfo_list[self.findexerGet(field_id)]
        calendarmap_list = fieldinfo_list['calendarmap_list']
        calendarmap_indexerGet = lambda x: dict((p['fieldday_id'],i) for i,p in enumerate(calendarmap_list)).get(x)
        return calendarmap_list[calendarmap_indexerGet(fieldday_id)]['date']

    def generateSchedule(self, totalmatch_list):
        tmindexerGet = lambda x: dict((p[IDPROPERTY_str],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.dbinterface.dropgame_docs()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            # flatten out the list embed div_id value in each dictionary
            # also flatten out 'GAME_TEAM' list generate by the match generator
            flatmatch_list = [{'ROUND_ID':z['round_id'], 'HOME':p['HOME'], 'AWAY':p['AWAY'], 'DIV_ID':x[IDPROPERTY_str]} for x in connecteddiv_match_list for y in x['match_list'] for z in y for p in z[GAME_TEAM_str]]
            # sort the list according to round_id (needed for groupby below), and then by div_id
            sorted_flatmatch_list = sorted(flatmatch_list, key=itemgetter('ROUND_ID', 'DIV_ID'))
            # group list by round_id; dict value of 'match_list' key is a nested array, which is created by an inner groupby based on div_id
            # The nested list will be passed to the roundrobin multiplexer
            #for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID')):
            #   for key1, items1 in groupby(items, key=itemgetter('DIV_ID')):
            #      for j in items1:
            #         print key, key1, j
            grouped_match_list = [{'round_id':rkey, 'match_list':[[{'home':x['HOME'], 'away':x['AWAY'], IDPROPERTY_str:dkey} for x in ditems] for dkey, ditems in groupby(ritems, key=itemgetter('DIV_ID'))]} for rkey, ritems in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            logging.debug("tournftscheduler:gensched:groupedlist=%s", grouped_match_list)
            #find the fields available for the connected_div_set by finding
            # the union of fields for each div
            # another option is to  call set.update (see fieldtimeschedule fset)
            fieldset = reduce(set.union,
                              map(set,[self.divinfo_list[self.dindexerGet(x)]['divfield_list'] for x in connected_div_list]))
            field_list = list(fieldset)
            max_slot_index = max(self.tfstatus_list[self.tfindexerGet(f)]['slotsperday'] for f in field_list)-1

            endtime_list = [(f,parser.parse(self.fieldinfo_list[self.findexerGet(f)]['end_time'])) for f in field_list]
            latest_endtime = max(endtime_list, key=itemgetter(1))[1]
            #field_cycle = cycle(fieldset)
            self.initTeamTimeGap_list(connected_div_list)
            '''
            if set(connected_div_list) == set(u10div_tuple):
                # if we are processing div U10, preallocate field time slots to each division (as they have different max rounds)
                self.reserveFieldTimeSlots(connected_div_list, field_list)
            '''
            current_fieldday_id = 1
            #earliestfield_list = None
            for round_games in grouped_match_list:
                #current_fieldday_id_list = [1,1]  # for U10
                #current_fieldday_id = 1
                round_id = round_games['round_id']
                round_match_list = round_games['match_list']
                if round_id > 1:
                    self.optimizeMatchOrder(round_match_list)
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    #current_fieldday_id_list = [1,1]  # for U10
                    #current_fieldday_id = 1
                    #earliestfield_list = None
                    div_id = rrgame[IDPROPERTY_str]
                    home = rrgame['home']
                    away = rrgame['away']
                    divinfo = self.divinfo_list[self.dindexerGet(div_id)]
                    ginterval = divinfo['gameinterval']
                    mingap_time = divinfo['mingap_time']
                    gameinterval = timedelta(0,0,0,0,ginterval)
                    nextmin_datetime = self.getcandidate_daytime(div_id, home, away, field_list, latest_endtime-gameinterval, mingap_time)
                    current_fieldday_id = search_tuple[0]
                    current_start = search_tuple[1]
                    # start time calc needs to be done here as start times for fields may change based on gameday
                    # if check in the list comprehension below exists as slotstatus_list[index] might be None if there is a closed_list
                    # (closed gameday list)
                    starttime_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]['sstatus_list'][0]['start_time']) for f in field_list if self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]]
                    found_tuple = self.findAlternateFieldSlot(field_list, current_fieldday_id, current_start, starttime_list, endtime_list, gameinterval, div_id, home, away)
                    #earliest_dict = earliestfield_list.pop()
                    #efield = earliest_dict['field_id']
                    #eslot = earliest_dict['index']
                    efield = found_tuple.field_id
                    eslot = found_tuple.slot_index
                    efieldday_id = found_tuple.fieldday_id
                    slotstatus_list = self.tfstatus_list[self.tfindexerGet(efield)]['slotstatus_list']
                    slotstatus_dict = slotstatus_list[efieldday_id-1]
                    game_date = slotstatus_dict['game_date']
                    selected_tfstatus = slotstatus_dict['sstatus_list'][eslot]
                    logging.debug("tournftscheduler:generate:assignment success rrgame %s gameday %d field %d slot %d", rrgame, efieldday_id, efield, eslot)
                    if selected_tfstatus['isgame']:
                        raise CodeLogicError("tournftscheduler:generate:game is already booked:")
                    selected_tfstatus['isgame'] = True
                    selected_tfstatus['teams'] = rrgame
                    #self.updateTeamTimeGap_list(div_id, home, away, efieldday_id, selected_tfstatus['start_time']+gameinterval)
                    self.updateTeamTimeGap_list(div_id, home, away, game_date,
                        selected_tfstatus['start_time']+gameinterval)
            for field_id in fieldset:
                for fieldday_id, slotstatus_list in enumerate(
                    self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list'], start=1):
                    if not slotstatus_list:
                        continue
                    game_date = slotstatus_list['game_date']
                    for match in slotstatus_list['sstatus_list']:
                        if match['isgame']:
                            start_time = match['start_time']
                            teams = match['teams']
                            div_id = teams[IDPROPERTY_str]
                            home_id = teams['home']
                            away_id = teams['away']
                            div = div = self.divinfo_list[self.dindexerGet(div_id)]
                            self.dbinterface.insertGameData(age=div['div_age'],
                                gen=div['div_gen'], fieldday_id=fieldday_id,
                                #game_date_str=game_date.strftime(date_format_CONST),
                                #start_time_str=gametime.strftime(time_format_CONST),
                                game_date=game_date, start_time=start_time,
                                venue=field_id, home=home_id, away=away_id)
                            '''
                            self.dbinterface.insertGameData(age=div.age,
                                gen=div.gender, fieldday_id,
                                start_time=gametime.strftime(time_format_CONST),
                                venue=field_id, home=home_id, away=away_id)
                            '''
        self.dbinterface.setsched_status()

    def getTournFieldSeasonStatus_list(self):
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldseason_status_list = []
        for f in self.fieldinfo_list:
            f_id = f['field_id']
            totalfielddays = f['tfd']
            gamestart = parser.parse(f['start_time'])
            end_time = parser.parse(f['end_time'])
            # take max for now - this is a simplification
            # default for phmsa is that divisions that share a field have
            # same game intervals
            ginterval = max(self.divinfo_list[self.dindexerGet(p)]['gameinterval'] for p in f['primaryuse_list'])
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
            slotstatus_list = totalfielddays*[None] #initialize
            for gameday in range(1,totalfielddays+1):
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

    def getFieldSeasonStatus_list(self):
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldstatus_list = []
        for f in self.fieldinfo_list:
            f_id = f['field_id']
            divinfo_list = [self.divinfo_list[self.dindexerGet(p)]
                for p in f['primaryuse_list']]
            #  if the field has multiple primary divisions, take max of gameinterval and gamesperseason
            max_interval = max(x['gameinterval'] for x in divinfo_list)
            gameinterval = timedelta(0,0,0,0,max_interval)  # convert to datetime compatible obj
            # get max of totalgamedays defined in divinfo config
            totalgamedays_list = [x['totalgamedays'] for x in divinfo_list]
            totalgamedays = max(totalgamedays_list)
            # number of days field is open every week
            totalfielddays = f['tfd']
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

    def findNextEarliestFieldSlot(self, field_list, cur_gameday, div_id):
        cur_gameday_ind = cur_gameday-1
        status_list = [(f,
                        self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday_ind]['sstatus_list'])
                        for f in field_list]
        if div_id in u10div_tuple:
            allindex_list = [(s[0],[i for i,j in enumerate(s[1]) if not j['isgame'] and j[IDPROPERTY_str]==div_id]) for s in status_list if not all(x['isgame'] for x in s[1])]
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
        #self.timegap_list = [{IDPROPERTY_str:self.divinfo_list[self.dindexerGet(x)][IDPROPERTY_str], 'team_id':y, 'last_end':-1, 'last_date':0} for x in div_list for y in range(1, self.divinfo_list[self.dindexerGet(x)]['totalteams']+1)]
        self.timegap_list.extend([{IDPROPERTY_str:x,
            'last_date':_absolute_earliest_date,
            'last_endtime':-1, 'team_id':y}
            for x in div_list for y in range(1, self.divinfo_list[self.dindexerGet(x)]['totalteams']+1)])
        # gapindexerGet must have a (div_id, team_id) tuple passed to it
        self.timegap_indexerGet = lambda x: [i for i,p in enumerate(self.timegap_list) if p[IDPROPERTY_str] == x[0] and p['team_id']==x[1]]

    def updateTeamTimeGap_list(self, div_id, home, away, game_date, endtime):
        for team in (home,away):
            gapindex_list = self.timegap_indexerGet((div_id, team))
            gapteam_dict = self.timegap_list[gapindex_list[0]]
            gapteam_dict['last_endtime'] = endtime.time()
            gapteam_dict['last_date'] = game_date.date()

    def getcandidate_daytime(self, div_id, home, away, field_list, latest_starttime,
        mingap_time):
        #minslot_gap = min_u10slotgap_CONST if div_id in (1,2) else min_slotgap_CONST
        homegap_dict = self.timegap_list[self.timegap_indexerGet((div_id, home))[0]]
        awaygap_dict = self.timegap_list[self.timegap_indexerGet((div_id, away))[0]]
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
            nextmin_datetime = maxgap_datetime + timedelta(minutes=mingap_time)
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

    def validateTimeSlot(self, div_id, field_id, gameday, slot_index, home, away):
        # check if candidate time slot has enough gap with the previously assigned slot for the two teams in the match
        target_slot = 0 # default return value
        target_gameday = gameday
        min_slotgap = min_u10slotgap_CONST if div_id in (1,2) else min_slotgap_CONST
        validate_flag = [False, False]
        target_tuple =  [-1,-1]
        for i, team in enumerate((home,away)):
            gapindex_list = self.timegap_indexerGet((div_id, team))
            if len(gapindex_list) != 1:
                raise CodeLogicError("tournftscheduler:initteamtimegap:gap list has multiple or No entries for div %d team %d indexlist %s" % (div_id, team, gapindex_list))
            gapteam_dict = self.timegap_list[gapindex_list[0]]
            gapslot = gapteam_dict['last_slot']
            gapday = gapteam_dict['last_date']
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
                    gapindex_list = self.timegap_indexerGet((div_id, team))
                    gapteam_dict = self.timegap_list[gapindex_list[0]]
                    gapteam_dict['last_slot'] = slot_index
                    gapteam_dict['last_date'] = gameday
            else:
                validate = False
                max_slot_index = len(self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list'][gameday-1])
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
        max_slot_index = max(self.tfstatus_list[self.tfindexerGet(f)]['slotsperday'] for f in field_list)-1
        slotstatus_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][gameday_ind]) for f in field_list]

        gamestart = min_start if target_start < min_start else target_start
        while gamestart + gameinterval <= max_end:
            s_set = set([s[0] for s in starttime_list if gamestart >= s[1]])
            e_set = set([e[0] for e in endtime_list if gamestart+gameinterval <= e[1]])
            f_list = list(s_set&e_set)
            limitedstatus_list = [s for s in slotstatus_list if s[0] in f_list]
            for limitedstatus in limitedstatus_list:
                #http://stackoverflow.com/questions/3694835/python-2-6-5-divide-timedelta-with-timedelta
                sstatus_list = limitedstatus[1]['sstatus_list']
                slot_index = int(ceil((gamestart - sstatus_list[0]['start_time']).total_seconds()/gameinterval_sec))
                if slot_index >= len(limitedstatus[1]):
                    continue
                if not sstatus_list[slot_index]['isgame']:
                    found_dict = {'field_id':limitedstatus[0],'slot_index':slot_index}
                    break
            else:
                gamestart += gameinterval
                continue
            break
        else:
            logging.debug("tournftscheduler:findaltfs:status_list is null gameday=%d target_start=%s div_id=%d home=%d away=%d",gameday, target_start, div_id, home, away)
            next_gameday = gameday + 1
            alt_list = None
            #while True or next_gameday > 3:
            while True:
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
                div_id = match[IDPROPERTY_str]
                home = match['home']
                away = match['away']
                #*********************#
                # cost calculation for ordering of matches
                # low cost if match has been scheduled earlier - cost is
                # sum of cost for home and away games.  gameday multiplied by 10
                # and added to slot number + 1 (because default slot is -1)
                #cost = sum(10*self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_date'] + self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_endtime'] +1 for x in (home,away))
                cost = sum(10*self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_date'] for x in (home,away))
                for x in (home,away):
                    last_end = self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_endtime']
                    if last_end != -1:
                    # note the difference against the earliest time or the division factor is not important - just needs to be consistent to calculate cost
                        cost += int(ceil((last_end - parser.parse('09:00')).total_seconds()/_min_timegap.total_seconds()))
                match['cost'] = cost
                #print 'cost match home away', cost, match, self.timegap_list[self.timegap_indexerGet((div_id, home))[0]], self.timegap_list[self.timegap_indexerGet((div_id, away))[0]]
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
            fstatus[1][gameday_ind][slot_index][IDPROPERTY_str] = div_id
