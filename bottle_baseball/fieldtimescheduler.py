from datetime import  datetime, timedelta
firstgame_starttime_CONST = datetime(2013,9,1,8,0,0)   # 8am on a dummy date
start_time_CONST = 'START_TIME'
from itertools import cycle
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
        # list hold per-field data structure of available time slots for scheduling
        # assume greeday algorithm for now
        for field in fieldinfo:
            self.scheduleMatrix.append({'field_id':field['field_id'],
                                        'next_available':field['start_time']})

    def generateSchedule(total_match_list):
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in total_match_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        match_list_indexer = dict((p['div_id'],i) for i,p in enumerate(total_match_list))
        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            sub_match_list = []
            for division in connected_div_list:
                fset.update(division['fields'])  #incremental union
                index = match_list_indexer.get(division)
                sub_match_list.append(total_match_list[index])
            flist = list(fset)
            flist.sort()  # default ordering, use it for now
            flist_citer = cycle(flist)

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
