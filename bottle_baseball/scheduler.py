from datetime import  datetime, timedelta
firstgame_starttime_CONST = datetime(2013,9,1,8,0,0)   # 8am on a dummy date
start_time_key_CONST = 'START_TIME'
venue_game_list_key_CONST = 'VENUE_GAME_LIST'
gameday_id_key_CONST = 'GAMEDAY_ID'
gameday_data_key_CONST = 'GAMEDAY_DATA'
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle

#http://www.tutorialspoint.com/python/python_classes_objects.htm
class ScheduleGenerator:
    def __init__(self, nt, nv, ginterval):
        self.numTeams = nt
        self.numVenues = nv
        #http://docs.python.org/2/library/datetime.html#timedelta-objects
        # see also python-in-nutshell
        # convert gameinterval into datetime.timedelta object
        self.game_interval = timedelta(0,0,0,0,ginterval)

    def generateRRSchedule(self):
        if (self.numTeams % 2):
            eff_numTeams = self.numTeams+1
            bye_flag = True
        else:
            eff_numTeams = self.numTeams
            bye_flag = False

        '''
        Implement circle method.  Circle iterates from 0 to one less than
        total number of effective teams.  Virtual team used if there is a bye.
        Outer loop emulates circle rotation (CCW)
        http://en.wikipedia.org/wiki/Round-robin_tournament
        http://mat.tepper.cmu.edu/trick/banff.ppt
        '''
        # define center (of circle) team - this will be fixed
        if (not bye_flag):
            circlecenter_team = eff_numTeams

        # outer loop emulates circle rotation there will be eff_numTeams-1 iterations
        # corresponds to number of game rotations, i.e. weeks (assuming there is one week per game)
        circle_total_pos = eff_numTeams - 1

        # half_n, num_time_slots, num_in_last_slot are variables relevant for schedule making
        # within a game day
        # half_n denotes number of positions on the scheduling circle, so it is independent
        # whether there is a bye or not
        half_n = eff_numTeams/2
        # if there is no bye, then the number of games per cycle equals half_n
        # if there is a bye, then the number of games equals half_n minus 1
        if (not bye_flag):
            numgames_per_cycle = half_n
        else:
            numgames_per_cycle = half_n - 1
        num_time_slots = numgames_per_cycle / self.numVenues  # number of time slots per day
        # number of games in time slot determined by number of venues,
        # but in last time slot not all venues may be used
        num_in_last_slot = numgames_per_cycle % self.numVenues

        total_round_list = []
        for rotation_ind in range(circle_total_pos):
            # each rotation_ind corresponds to a single game cycle (a week if there is one game per week)
            circletop_team = rotation_ind + 1   # top of circle

            # initialize dictionary that will contain data on the current game cycle's matches.
            # Game cycle number (week number if there is only one game per week)
            # is the same as the circletop_team number
            single_gameday_dict = {gameday_id_key_CONST:circletop_team}

            # first game pairing
            if (not bye_flag):
                round_list = [(circletop_team, circlecenter_team)]
            else:
                round_list = []
            for j in range(1, half_n):
                # we need to loop for the n value (called half_n)
                # which is half of effective number of teams (which includes bye team if
                # there is one)
                # But depending on number of venues we are going to have to play multiple games
                # in a day (hence the schedule)
                # ------------------
                # logic assumes teams are numbered from 1,..,circle_total_pos,
                # the latter also being the %mod operator value
                # first subtract 1 to recover 0-based index
                # then either subtract or add the increment value (depending on whether
                # we are on the left or right side of the circle
                # get modulus
                # then increment by one to get 1-based index (team number)
                CCW_team = (((circletop_team-1)-j) % circle_total_pos)+1
                CW_team = (((circletop_team-1)+j) % circle_total_pos) + 1
                round_list.append((CCW_team, CW_team))

            # Given the list of the games for a single game cycle, break up the list into
            # sublists.  Each sublist represent games that are played at a particular time.
            # Do the list-sublist partition after the games have been determined above, as dealing
            # with the first game (top of circle vs center of circle/bye) presents too many special cases
            single_gameday_list = []
            gametime = firstgame_starttime_CONST
            ind = 0;
            for timeslot in range(num_time_slots):
                timeslot_dict = {}
                timeslot_game_list = []
                for v in range(self.numVenues):
                    timeslot_game_list.append(round_list[ind])
                    ind += 1
                # create dictionary entries for formatted game time as string and venue game list
                # format is 12-hour hour:minutes
                timeslot_dict[start_time_key_CONST] = gametime.strftime('%I:%M')
                timeslot_dict[venue_game_list_key_CONST] = timeslot_game_list
                gametime += self.game_interval
                single_gameday_list.append(timeslot_dict)

            if (num_in_last_slot):
                # if there are games to be played in the last slot (less than number of venues)
                timeslot_dict = {}
                timeslot_game_list = []
                for v in range(num_in_last_slot):
                    timeslot_game_list.append(round_list[ind])
                    ind += 1
                timeslot_dict[start_time_key_CONST] = gametime.strftime('%I:%M')
                timeslot_dict[venue_game_list_key_CONST] = timeslot_game_list
                single_gameday_list.append(timeslot_dict)

            single_gameday_dict[gameday_data_key_CONST] = single_gameday_list
            if (bye_flag):
                # if bye flag is enabled, then team at the top of 'circle' has bye.
                # Note we are sending over the bye team info, but currently the UI is not
                # displaying it (need to figure out where to display it)
                single_gameday_dict[bye_CONST] = circletop_team
            # once dictionary element containing all data for the game cycle is created,
            # append that dict element to the total round list
            total_round_list.append(single_gameday_dict)

        print "total round list=",total_round_list
        return total_round_list

    def MeasureHomeAway():
