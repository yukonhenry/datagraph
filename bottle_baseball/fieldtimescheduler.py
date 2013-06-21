from datetime import  datetime, timedelta
from itertools import cycle
from schedule_util import roundrobin, all_same
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision
firstgame_starttime_CONST = datetime(2013,9,1,8,0,0)   # 8am on a dummy date
start_time_CONST = 'START_TIME'
venue_game_list_CONST = 'VENUE_GAME_LIST'
gameday_id_CONST = 'GAMEDAY_ID'
gameday_data_CONST = 'GAMEDAY_DATA'
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
homeaway_CONST = 'HOMEAWAY'
home_CONST = 'HOME'
away_CONST = 'AWAY'
venue_count_CONST = 'VCNT'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
venue_CONST = 'VENUE'
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
#http://www.tutorialspoint.com/python/python_classes_objects.htm
class FieldTimeScheduleGenerator:
    def __init__(self, leaguedivinfo, fieldinfo, connected_comp):
        self.leaguedivinfo = leaguedivinfo
        self.connected_div_components = connected_comp
        self.scheduleMatrix = []
        self.fieldinfo = fieldinfo
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.leaguedivinfo)+1):
            self.total_game_dict[i] = []

        # assume greeday algorithm for now
        for field in fieldinfo:
            self.scheduleMatrix.append({'field_id':field['field_id'],
                                        'next_available':field['start_time']})

    def generateSchedule(self, total_match_list):
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in total_match_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        # indexer below is used to protect against list of dictionaries that are not ordered according to id,
        # though it is a protective measure, as the list should be ordered with the id.
        match_list_indexer = dict((p['div_id'],i) for i,p in enumerate(total_match_list))
        leaguediv_indexer = dict((p['div_id'],i) for i,p in enumerate(self.leaguedivinfo))
        fieldinfo_indexer = dict((p['field_id'],i) for i,p in enumerate(self.fieldinfo))

        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            submatch_list = []
            submatch_len_list = []
            gameinterval_dict = {}
            for division in connected_div_list:
                divindex = leaguediv_indexer.get(division)
                fset.update(self.leaguedivinfo[divindex]['fields'])  #incremental union
                # http://docs.python.org/2/library/datetime.html#timedelta-objects
                # see also python-in-nutshell
                # convert gameinterval into datetime.timedelta object
                ginterval = self.leaguedivinfo[divindex]['gameinterval']
                gameinterval_dict[division] = timedelta(0,0,0,0,ginterval)
                index = match_list_indexer.get(division)
                submatch_list.append(total_match_list[index])
                submatch_len_list.append(len(total_match_list[index]['match_list']))
            if not all_same(submatch_len_list):
                print 'different number of games per season amongst shared field NOT SUPPORTED'
                return None

            flist = list(fset)
            flist.sort()  # default ordering, use it for now
            field_list = []
            initialstarttime_dict = {}
            for f_id in flist:
                # field_id is 0-index based
                findex = fieldinfo_indexer.get(f_id)
                # note convert start time string to datetime obj
                nexttime_dtime = parser.parse(self.fieldinfo[findex]['start_time'])
                field_list.append({'field_id':f_id,
                                   'next_time':nexttime_dtime})
                initialstarttime_dict[f_id] = nexttime_dtime  #use for resetting time to beginning of day
            print 'fieldlist', field_list
            # max below is not sufficient if there are differences in season per games
            # within the divisions that share fields
            for round_index in xrange(max(submatch_len_list)):
                combined_match_list = []
                gameday_dict = {}
                for division_dict in submatch_list:
                    div_id = division_dict['div_id']
                    match_list = division_dict['match_list'][round_index]
                    round_id = match_list[round_id_CONST]
                    print 'round id', round_id
                    gameday_dict[div_id] = []
                    game_list = match_list[game_team_CONST]
                    round_match_list = []
                    for game in game_list:
                        round_match_list.append({'div_id':div_id, 'game':game,
                                                 'gameinterval':gameinterval_dict[div_id]})
                    combined_match_list.append(round_match_list)
                # mutliplex the divisions that are sharing fields; user itertools round robin utility
                #http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
                # http://stackoverflow.com/questions/7529376/pythonic-way-to-mix-two-lists
                rrgenobj = roundrobin(combined_match_list)
                field_list_iter = cycle(field_list)
                field = field_list_iter.next()
                for rrgame in rrgenobj:
                    print 'rr',rrgame, field, field['next_time'].strftime(time_format_CONST)
                    div = getAgeGenderDivision(rrgame['div_id'])
                    print 'division', div.age, div.gender
                    gameday_dict[rrgame['div_id']].append({game_team_CONST:rrgame['game'],
                                                           start_time_CONST:field['next_time'].strftime(time_format_CONST),
                                                           venue_CONST:field['field_id']})
                    # update next available time for the field
                    field['next_time'] += rrgame['gameinterval']
                    field = field_list_iter.next()
                self.total_game_dict[div_id].append({gameday_id_CONST:round_id, gameday_data_CONST:gameday_data_list})
                # reset next available time for new round
                for f in field_list:
                    f['next_time'] = initialstarttime_dict[field['field_id']]
        print self.total_game_dict

    def generateRRSchedule(self, conflict_ind=0):
        self.generateRoundMatchList()
        # if there is no bye, then the number of games per cycle equals half_n
        # if there is a bye, then the number of games equals half_n minus 1
        if (not self.bye_flag):
            numgames_per_cycle = self.half_n
        else:
            numgames_per_cycle = self.half_n - 1
        num_time_slots = numgames_per_cycle / self.numVenues  # number of time slots per day
        # number of games in time slot determined by number of venues,
        # but in last time slot not all venues may be used
        num_in_last_slot = numgames_per_cycle % self.numVenues

        # fill in timeslots
        if (num_in_last_slot):
            self.timeslots_per_day = num_time_slots
        else:
            self.timeslots_per_day = num_time_slots + 1

        total_game_list = []
        for round_dict in self.games_by_round_list:
            game_list = round_dict[game_team_CONST]
            round_id = round_dict[round_id_CONST]
            # initialize dictionary that will contain data on the current game cycle's matches.
            # Game cycle number (week number if there is only one game per week)
            # is the same as the circletop_team number
            single_gameday_dict = {gameday_id_CONST:round_id}

            # Given the list of the games for a single game cycle, break up the list into
            # sublists.  Each sublist represent games that are played at a particular time.
            # Do the list-sublist partition after the games have been determined above, as dealing
            # with the first game (top of circle vs center of circle/bye) presents too many special cases
            single_gameday_list = []
            if conflict_ind == 0:
                gametime = firstgame_starttime_CONST
            else:
                # offset start time
                gametime = firstgame_starttime_CONST + self.game_interval * conflict_ind
            ind = 0;
            for timeslot in range(num_time_slots):
                timeslot_dict = {}
                timeslot_game_list = []
                for v in range(self.numVenues):
                    timeslot_game_list.append({venue_CONST:self.venues[v],
                                               game_team_CONST:game_list[ind]})
                    self.metrics_list[game_list[ind][home_CONST]-1][venue_count_CONST][v] += 1
                    self.metrics_list[game_list[ind][away_CONST]-1][venue_count_CONST][v] += 1
                    ind += 1
                # create dictionary entries for formatted game time as string and venue game list
                timeslot_dict[start_time_CONST] = gametime.strftime(time_format_CONST)
                timeslot_dict[venue_game_list_CONST] = timeslot_game_list
                gametime += self.gap_on_field
                single_gameday_list.append(timeslot_dict)

            if (num_in_last_slot):
                # if there are games to be played in the last slot (less than number of venues)
                timeslot_dict = {}
                timeslot_game_list = []
                for v in range(num_in_last_slot):
                    timeslot_game_list.append({venue_CONST:self.venues[v],
                                               game_team_CONST:game_list[ind]})
                    self.metrics_list[game_list[ind][home_CONST]-1][venue_count_CONST][v] += 1
                    self.metrics_list[game_list[ind][away_CONST]-1][venue_count_CONST][v] += 1
                    ind += 1
                timeslot_dict[start_time_CONST] = gametime.strftime(time_format_CONST)
                timeslot_dict[venue_game_list_CONST] = timeslot_game_list
                single_gameday_list.append(timeslot_dict)

            single_gameday_dict[gameday_data_CONST] = single_gameday_list
            if (self.bye_flag):
                # if bye flag is enabled, then team at the top of 'circle' has bye.
                # Note we are sending over the bye team info, but currently the UI is not
                # displaying it (need to figure out where to display it)
                single_gameday_dict[bye_CONST] = round_id
            # once dictionary element containing all data for the game cycle is created,
            # append that dict element to the total round list
            total_game_list.append(single_gameday_dict)

        #print "total round list=",total_game_list
        return total_game_list
