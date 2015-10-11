''' Copyright YukonTR 2013 '''

from itertools import groupby, cycle
from operator import itemgetter
from util.schedule_util import roundrobin, enum, shift_list, \
    getConnectedDivisionGroup, all_isless, find_ge, find_le, all_same
from datetime import datetime, timedelta, date
from dateutil import parser
from copy import deepcopy
from collections import namedtuple
from util.sched_exceptions import FieldAvailabilityError, TimeSlotAvailabilityError, FieldTimeAvailabilityError, CodeLogicError, SchedulerConfigurationError
import logging
from math import ceil
from pprint import pprint
from random import shuffle
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
_ScheduleParam = namedtuple('SchedParam', 'field_id fieldday_id slot_index')
time_format_CONST = '%H:%M'
_absolute_earliest_time = parser.parse('05:00').time()
_absolute_earliest_date = parser.parse('01/01/2010').date()
_min_timegap = timedelta(0,0,0,0,160) # in minutes
# Current implementation for elimination tournaments has the intergame gap for
# each team satisfy the minimum time gap, i.e. matches are scheduled to
# complete as soon as possible (greedy time-wise) as long as various
# constraints are satisfied.  If we want to arbitrarily stretch out the
# schedule, e.g. matches for a particular round should fall on a certain
# (later than necessary date), then define _force_absround_to_fieldday_list,
# with a list-implied mapping from round# (list index+1) to fieldday_id
# Eventually UI support will be required.
#_force_absround_to_fieldday_list = [{'div_id':1, 'fieldday_map':[1,2,2]}]
#_findexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(_force_absround_to_fieldday_list)).get(x)
class TournamentFieldTimeScheduleGenerator:
    def __init__(self, dbinterface, divinfo_tuple, fieldinfo_tuple,
        tourn_type='RR'):
        self.dbinterface = dbinterface
        self.tourn_type = tourn_type
        if tourn_type == 'elimination':
            self.idproperty = 'div_id'
        elif tourn_type == 'RR':
            self.idproperty = 'tourndiv_id'
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.connected_div_components = getConnectedDivisionGroup(self.fieldinfo_list)
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        #tfstatus_tuple = self.getTournFieldSeasonStatus_list()
        fstatus_tuple = self.getFieldSeasonStatus_list()
        self.tfstatus_list = fstatus_tuple.dict_list
        self.tfindexerGet = fstatus_tuple.indexerGet
        self.timegap_list = []
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
        tmindexerGet = lambda x: dict((p[self.idproperty],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.dbinterface.dropgame_docs()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            # flatten out the list embed div_id value in each dictionary
            # also flatten out 'GAME_TEAM' list generate by the match generator
            flatmatch_list = [{'ROUND_ID':z['round_id'], 'HOME':p['HOME'], 'AWAY':p['AWAY'], 'DIV_ID':x[self.idproperty]} for x in connecteddiv_match_list for y in x['match_list'] for z in y for p in z['game_team']]
            # sort the list according to round_id (needed for groupby below), and then by div_id
            sorted_flatmatch_list = sorted(flatmatch_list, key=itemgetter('ROUND_ID', 'DIV_ID'))
            # group list by round_id; dict value of 'match_list' key is a nested array, which is created by an inner groupby based on div_id
            # The nested list will be passed to the roundrobin multiplexer
            #for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID')):
            #   for key1, items1 in groupby(items, key=itemgetter('DIV_ID')):
            #      for j in items1:
            #         print key, key1, j
            grouped_match_list = [{'round_id':rkey, 'match_list':[[{'home':x['HOME'], 'away':x['AWAY'], self.idproperty:dkey} for x in ditems] for dkey, ditems in groupby(ritems, key=itemgetter('DIV_ID'))]} for rkey, ritems in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            logging.debug("tournftscheduler:gensched:groupedlist=%s", grouped_match_list)
            #find the fields available for the connected_div_set by finding
            # the union of fields for each div
            # another option is to  call set.update (see fieldtimeschedule fset)
            fieldset = reduce(set.union,
                              map(set,[self.divinfo_list[self.dindexerGet(x)]['divfield_list'] for x in connected_div_list]))
            field_list = list(fieldset)
            #max_slot_index = max(self.tfstatus_list[self.tfindexerGet(f)]['slotsperday'] for f in field_list)-1

            endtime_list = [(f,parser.parse(self.fieldinfo_list[self.findexerGet(f)]['end_time'])) for f in field_list]
            latest_endtime = max(endtime_list, key=itemgetter(1))[1]
            #field_cycle = cycle(fieldset)
            self.initTeamTimeGap_list(connected_div_list)
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
                    div_id = rrgame[self.idproperty]
                    home = rrgame['home']
                    away = rrgame['away']
                    divinfo = self.divinfo_list[self.dindexerGet(div_id)]
                    ginterval = divinfo['gameinterval']
                    mingap_time = divinfo['mingap_time']
                    gameinterval = timedelta(0,0,0,0,ginterval)
                    # get absolute datetime that satisfies gaptime requirement
                    nextmin_datetime = self.getcandidate_daytime(div_id, home, away, latest_endtime-gameinterval, mingap_time)
                    # get earliest date for each field that satisfies nextmin_datetime requirement
                    mindate_tuple = self.getmindate_tuple(nextmin_datetime, field_list)
                    # group them according to date
                    datesortedfield_list = self.datesort_fields(mindate_tuple,
                        field_list)
                    #current_fieldday_id = search_tuple[0]
                    #current_start = search_tuple[1]
                    # start time calc needs to be done here as start times for fields may change based on gameday
                    # if check in the list comprehension below exists as slotstatus_list[index] might be None if there is a closed_list
                    # (closed gameday list)
                    #starttime_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]['sstatus_list'][0]['start_time']) for f in field_list if self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]]
                    earliest_dict = self.findAlternateFieldSlot(field_list,
                        endtime_list, gameinterval, div_id, home, away,
                        nextmin_datetime, datesortedfield_list)
                    efield = earliest_dict['field_id']
                    eslot = earliest_dict['slot_index']
                    efieldday_id = earliest_dict['fieldday_id']
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
                        selected_tfstatus['start_time']+gameinterval, efieldday_id)
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
                            div_id = teams[self.idproperty]
                            home_id = teams['home']
                            away_id = teams['away']
                            div = self.divinfo_list[self.dindexerGet(div_id)]
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
        return True

    def generateElimSchedule(self, totalmatch_list):
        tmindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.dbinterface.dropgame_docs()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            # Also combine the separate lists corresponding to each division into
            # one large division
            connecteddiv_matchrange_list = [{'div_id':totalmatch_list[tmindexerGet(x)]['div_id'],
                'match_id_range':totalmatch_list[tmindexerGet(x)]['match_id_range']} for x in connected_div_list]
            connecteddiv_match_list = [y for x in connected_div_list
                for y in totalmatch_list[tmindexerGet(x)]['divmatch_list']]
            sorted_match_list = sorted(connecteddiv_match_list, key=itemgetter('absround_id', 'btype'))
            grouped_match_list = [{'absround_id':arkey,'match_list':[[{'home':y['home'], 'away':y['away'], 'div_id':y['div_id'], 'match_id':y['match_id'], 'comment':y['comment'], 'round':y['round']} for y in x['match_list']] for x in aritems]} for arkey, aritems in groupby(sorted_match_list,key=itemgetter('absround_id'))]
            for x in grouped_match_list:
                logging.debug("elimftsched:gen: grouped elem %s", x)

            #find the fields available for the connected_div_set by finding
            # the union of fields for each div
            # another option is to  call set.update (see fieldtimeschedule fset)
            fieldset = reduce(set.union,
                              map(set,[self.divinfo_list[self.dindexerGet(x)]['divfield_list'] for x in connected_div_list]))
            field_list = list(fieldset)
            endtime_list = [(f,parser.parse(self.fieldinfo_list[self.findexerGet(f)]['end_time'])) for f in field_list]
            latest_endtime = max(endtime_list, key=itemgetter(1))[1]
            self.initElimTeamTimeGap_list(connecteddiv_matchrange_list)
            current_fieldday_id = 1
            #earliestfield_list = None
            for round_games in grouped_match_list:
                #current_fieldday_id_list = [1,1]  # for U10
                #current_fieldday_id = 1
                absround_id = round_games['absround_id']
                round_match_list = round_games['match_list']
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    #current_fieldday_id_list = [1,1]  # for U10
                    #current_fieldday_id = 1
                    #earliestfield_list = None
                    div_id = rrgame['div_id']
                    home = rrgame['home']
                    away = rrgame['away']
                    match_id = rrgame['match_id']
                    divinfo = self.divinfo_list[self.dindexerGet(div_id)]
                    ginterval = divinfo['gameinterval']
                    mingap_time = divinfo['mingap_time']
                    gameinterval = timedelta(0,0,0,0,ginterval)
                    elimination_type = divinfo['elimination_type']
                    # get absolute datetime that satisfies gaptime requirement
                    nextmin_datetime = self.getElimcandidate_daytime(div_id, home, away, field_list, latest_endtime-gameinterval, mingap_time,
                        absround_id, elimination_type)
                    # get earliest date for each field that satisfies nextmin_datetime requirement
                    mindate_tuple = self.getmindate_tuple(nextmin_datetime, field_list)
                    # group them according to date
                    datesortedfield_list = self.datesort_fields(mindate_tuple,
                        field_list)
                    #current_fieldday_id = search_tuple[0]
                    #current_start = search_tuple[1]
                    # start time calc needs to be done here as start times for fields may change based on gameday
                    # if check in the list comprehension below exists as slotstatus_list[index] might be None if there is a closed_list
                    # (closed gameday list)
                    #starttime_list = [(f,self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]['sstatus_list'][0]['start_time']) for f in field_list if self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][current_fieldday_id-1]]
                    earliest_dict = self.findAlternateFieldSlot(field_list,
                        endtime_list, gameinterval, div_id, home, away,
                        nextmin_datetime, datesortedfield_list)
                    efield = earliest_dict['field_id']
                    eslot = earliest_dict['slot_index']
                    efieldday_id = earliest_dict['fieldday_id']
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
                    self.updateElimMatchTimeGap_list(div_id, game_date,
                        selected_tfstatus['start_time']+gameinterval,
                        efieldday_id, match_id)
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
                            div_id = teams['div_id']
                            home_id = teams['home']
                            away_id = teams['away']
                            match_id = teams['match_id']
                            comment = teams['comment']
                            around = teams['round']
                            div = self.divinfo_list[self.dindexerGet(div_id)]
                            self.dbinterface.insertElimGameData(age=div['div_age'],
                                gen=div['div_gen'], fieldday_id=fieldday_id,
                                #game_date_str=game_date.strftime(date_format_CONST),
                                #start_time_str=gametime.strftime(time_format_CONST),
                                game_date=game_date, start_time=start_time,
                                venue=field_id, home=home_id, away=away_id,
                                match_id=match_id, comment=comment, around=around)
                            '''
                            self.dbinterface.insertGameData(age=div.age,
                                gen=div.gender, fieldday_id,
                                start_time=gametime.strftime(time_format_CONST),
                                venue=field_id, home=home_id, away=away_id)
                            '''
        self.dbinterface.setsched_status()
        return True

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
            if self.tourn_type == 'RR' and totalfielddays < totalgamedays:
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
                    slotstatus_dict['slotsperday'] = len(lstatus_list)
                else:
                    slotstatus_dict['sstatus_list'] = deepcopy(sstatus_list)
                    slotstatus_dict['slotsperday'] = sstatus_len
                slotstatus_list.append(slotstatus_dict)
            # ref http://stackoverflow.com/questions/4260280/python-if-else-in-list-comprehension for use of if-else in list comprehension
            fieldstatus_list.append({'field_id':f['field_id'],
                'slotstatus_list':slotstatus_list})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldstatus_list)).get(x)
        List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
        return List_Indexer(fieldstatus_list, fstatus_indexerGet)

    def initTeamTimeGap_list(self, div_list):
        for div_id in div_list:
            '''
            if div_id == 2:
                self.timegap_list.extend([{self.idproperty:div_id,
                    'last_date':_absolute_earliest_date, 'fieldday_id':0,
                    'last_endtime':-1, 'team_id':y}
                    for y in range(1, 18)+range(19,23)])
            '''
            self.timegap_list.extend([{self.idproperty:div_id,
                'last_date':_absolute_earliest_date, 'fieldday_id':0,
                'last_endtime':-1, 'team_id':y}
                for y in range(1, self.divinfo_list[self.dindexerGet(div_id)]['totalteams']+1)])

        # gapindexerGet must have a (div_id, team_id) tuple passed to it
        self.timegap_indexerGet = lambda x: [i for i,p in enumerate(self.timegap_list) if p[self.idproperty] == x[0] and p['team_id']==x[1]]

    def initElimTeamTimeGap_list(self, matchrange_list):
        self.timegap_list.extend([{'div_id':x['div_id'],
            'last_date':_absolute_earliest_date, 'fieldday_id':0,
            'last_endtime':-1, 'team_id':y}
            for x in matchrange_list for y in range(x['match_id_range'][0],
                x['match_id_range'][1]+1)])
        # gapindexerGet must have a (div_id, team_id) tuple passed to it
        self.timegap_indexerGet = lambda x: [i for i,p in enumerate(self.timegap_list) if p['div_id'] == x[0] and p['team_id']==x[1]]

    def updateTeamTimeGap_list(self, div_id, home, away, game_date, endtime, fieldday_id):
        for team in (home,away):
            gapindex_list = self.timegap_indexerGet((div_id, team))
            gapteam_dict = self.timegap_list[gapindex_list[0]]
            gapteam_dict['last_endtime'] = endtime.time()
            gapteam_dict['last_date'] = game_date.date()
            gapteam_dict['fieldday_id'] = fieldday_id

    def updateElimMatchTimeGap_list(self, div_id, game_date, endtime,
        fieldday_id, match_id):
        gapindex_list = self.timegap_indexerGet((div_id, match_id))
        gapteam_dict = self.timegap_list[gapindex_list[0]]
        gapteam_dict['last_endtime'] = endtime.time()
        gapteam_dict['last_date'] = game_date.date()
        gapteam_dict['fieldday_id'] = fieldday_id

    def getcandidate_daytime(self, div_id, home, away, latest_starttime,
        mingap_time):
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

    def getElimcandidate_daytime(self, div_id, home, away, field_list,
        latest_starttime, mingap_time, absround_id, elimination_type):
        team_list = [int(t[1:]) for t in (home, away) if t[0] !='S']
        if team_list:
            teamgap_date_list = [self.timegap_list[self.timegap_indexerGet((div_id, team))[0]]['last_date'] for team in team_list]
            teamgap_endtime_list = [self.timegap_list[self.timegap_indexerGet((div_id, team))[0]]['last_endtime'] for team in team_list]
            if all_same(teamgap_date_list):
                maxgap_date = teamgap_date_list[0]
                maxgap_endtime= max(teamgap_endtime_list)
            else:
                maxgap_date = max(teamgap_date_list)
                max_ind = [i for i,j in enumerate(teamgap_date_list) if j==maxgap_date]
                maxgap_endtime = max([teamgap_endtime_list[i] for i in max_ind])
            if maxgap_date == _absolute_earliest_date:
                next_start = _absolute_earliest_time
                # get equivalent datetime object
                nextmin_datetime = datetime.combine(maxgap_date, next_start)
            else:
                maxgap_datetime = datetime.combine(maxgap_date, maxgap_endtime)
                nextmin_datetime = maxgap_datetime + timedelta(minutes=mingap_time)
                if nextmin_datetime.time() > latest_starttime.time():
                    # get time from the next_datetime - if it exceeds the latest allowable
                    # time, increment date and set time to earliest time
                    next_date = nextmin_datetime.date() + timedelta(days=1)
                    next_start = _absolute_earliest_time
                    nextmin_datetime = datetime.combine(next_date, next_start)
            if elimination_type == 'S' and "_force_absround_to_fieldday_list" in globals():
                # for single elimination tournament, if there is a force-fieldday
                # map defined for the division:
                findex = _findexerGet(div_id)
                if findex is not None:
                    # get the target fieldday for the abs round (subtract 1 to
                    # index in)
                    target_fieldday = _force_absround_to_fieldday_list[findex]['fieldday_map'][absround_id-1]
                    # find the earliest calendar date corresponding to the fieldday
                    # mapped for each field in field_list
                    min_target_date = min(self.mapfieldday_datetime(f,
                        target_fieldday) for f in field_list).date()
                    if nextmin_datetime.date() < min_target_date:
                        # if the calculated next min datetime is earlier than the
                        # target date derived from the force-fieldday map, then
                        # push the next min datetime to that target date
                        nextmin_datetime = datetime.combine(min_target_date,
                            _absolute_earliest_time)
        else:
            next_date = _absolute_earliest_date
            next_start = _absolute_earliest_time
            nextmin_datetime = datetime.combine(next_date, next_start)
        return nextmin_datetime

    def getmindate_tuple(self, nextmin_datetime, field_list):
        mindate_list = []
        for field_id in field_list:
            minfieldday_id, min_date = self.mapdatetime_fieldday(field_id,
                nextmin_datetime, key='min')
            mindate_dict = {'field_id':field_id,
                'fieldday_id':minfieldday_id, 'date':min_date}
            mindate_list.append(mindate_dict)
            # get other dates for this field
            slotstatus_list = self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list']
            # next fieldday index is minfieldday_id-1 + 1 = minfieldday_id
            nextfieldday_index = minfieldday_id
            for slotstatus_dict in slotstatus_list[nextfieldday_index:]:
                mindate_dict = {'field_id':field_id, 'fieldday_id':slotstatus_dict['fieldday_id'], 'date':slotstatus_dict['game_date']}
                mindate_list.append(mindate_dict)
        # sort according to date
        mindexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(mindate_list)).get(x)
        return _List_Indexer(mindate_list, mindexerGet)

    def datesort_fields(self, mindate_tuple, field_list):
        mindate_list = mindate_tuple.dict_list
        mindexerGet = mindate_tuple.indexerGet
        mindate_list.sort(key=itemgetter('date'))
        dategroup = groupby(mindate_list, key=itemgetter('date'))
        datesortedfield_list = [{'date':k,
            'field_list':[{'field_id':x['field_id'], 'fieldday_id':x['fieldday_id']} for x in v]} for k, v in dategroup]
        return datesortedfield_list

    def findAlternateFieldSlot(self, field_list, endtime_list, gameinterval,
        div_id, home, away, nextmin_datetime, datesortedfield_list):
        target_start_time = nextmin_datetime.time()
        gameinterval_sec = gameinterval.total_seconds()
        slot_list = list()
        pprint(datesortedfield_list)
        for dsfield_dict in datesortedfield_list:
            game_date = dsfield_dict['date']
            datefield_list = dsfield_dict['field_list']
            for datefield in datefield_list:
                field_id = datefield['field_id']
                fieldday_id = datefield['fieldday_id']
                slotstatus_list = self.tfstatus_list[self.tfindexerGet(field_id)]['slotstatus_list']
                slotstatus_dict = slotstatus_list[fieldday_id-1]
                slotsperday = slotstatus_dict['slotsperday']
                sstatus_list = slotstatus_list[fieldday_id-1]['sstatus_list']
                for slot_index in range(slotsperday):
                    sstatus_dict = sstatus_list[slot_index]
                    start_time = sstatus_dict['start_time']
                    if not sstatus_dict['isgame'] and start_time.time() >= target_start_time:
                        break
                else:
                    # got to next field
                    continue
                slot_dict = {'slot_index':slot_index, 'field_id':field_id,
                    'game_date':game_date, 'start_time':start_time,
                    'fieldday_id':fieldday_id}
                slot_list.append(slot_dict)
            if slot_list:
                break
            else:
                # if the date rolls over, target_start_time is at the earliest time
                target_start_time = _absolute_earliest_time
        slot_list.sort(key=itemgetter('game_date', 'start_time', 'field_id'))
        pprint(slot_list)
        return slot_list[0]

    def optimizeMatchOrder(self, rmlist):
        #print 'gameday', gameday
        for divmatch_list in rmlist:
            #print 'divmatch', divmatch_list
            for match in divmatch_list:
                div_id = match[self.idproperty]
                home = match['home']
                away = match['away']
                #*********************#
                # cost calculation for ordering of matches
                # low cost if match has been scheduled earlier - cost is
                # sum of cost for home and away games.  gameday multiplied by 10
                # and added to slot number + 1 (because default slot is -1)
                #cost = sum(10*self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_date'] + self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_endtime'] +1 for x in (home,away))
                cost = sum(10*self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['fieldday_id'] for x in (home,away))
                for x in (home,away):
                    last_endtime = self.timegap_list[self.timegap_indexerGet((div_id, x))[0]]['last_endtime']
                    if last_endtime != -1:
                    # note the difference against the earliest time or the division factor is not important - just needs to be consistent to calculate cost
                        last_endtime_dt = datetime.combine(date.today(),
                            last_endtime)
                        cost += int(ceil((last_endtime_dt - parser.parse('08:00')).total_seconds()/_min_timegap.total_seconds()))
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
            fstatus[1][gameday_ind][slot_index][self.idproperty] = div_id
