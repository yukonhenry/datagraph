from datetime import  datetime, timedelta
firstgame_starttime = datetime(2013,9,1,8,0,0)   # 8am on a dummy date
start_time_key_CONST = 'START_TIME'
venue_game_list_key_CONST = 'VENUE_GAME_LIST'

def generateRRSchedule(numTeams, numVenues, ginterval):
    #http://docs.python.org/2/library/datetime.html#timedelta-objects
    # see also python-in-nutshell
    # convert gameinterval into datetime.timedelta object
    game_interval = timedelta(0,0,0,0,ginterval)

    if (numTeams % 2):
        eff_numTeams = numTeams+1
        bye_flag = True
    else:
        eff_numTeams = numTeams
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
    else:
        circlecenter_team = 'bye'  # check later if string will be accepted

    # outer loop emulates circle rotation there will be eff_numTeams-1 iterations
    # corresponds to number of game rotations, i.e. weeks (assuming there is one week per game)
    circle_total_pos = eff_numTeams - 1

    # half_n, num_time_slots, num_in_last_slot are variables relevant for schedule making
    # within a game day
    half_n = eff_numTeams/2
    num_time_slots = half_n / numVenues  # number of time slots per day
    # number of games in time slot determined by number of venues,
    # but in last time slot not all venues may be used
    num_in_last_slot = half_n % numVenues

    total_round_list = []
    for rotation_ind in range(circle_total_pos):
        # each rotation_ind corresponds to a single game cycle (a week if there is one game per week)
        circletop_team = rotation_ind + 1   # top of circle
        # first game pairing
        round_list = [(circletop_team, circlecenter_team)]
        '''
        j = 1 # j var will iterate from 1 to half_n-1 (games per game cycle)
        for timeslot in range(num_time_slots):
            timeslot_game_list = []
            for v in range(numVenues):
                CCW_team = (((circletop_team-1)-j) % circle_total_pos) + 1
                CW_team = (((circletop_team-1)+j) % circle_total_pos) + 1
                j += 1
                timeslot_game_list.append((CCW_team, CW_team))
            round_list.append(timeslot_game_list)
        if (num_in_last_slot):
            timeslot_game_list = []
            for v in range(num_in_last_slot):
                CCW_team = (((circletop_team-1)-j) % circle_total_pos) + 1
                CW_team = (((circletop_team-1)+j) % circle_total_pos) + 1
                j += 1
                timeslot_game_list.append((CCW_team, CW_team))
            round_list.append(timeslot_game_list)
        '''
        for j in range(1, half_n):
            # we need to loop for the n value (called half_n) which is half of effective
            # number of teams.
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
        single_game_cycle_list = []
        gametime = firstgame_starttime
        ind = 0;
        for timeslot in range(num_time_slots):
            timeslot_obj = {}
            timeslot_game_list = []
            for v in range(numVenues):
                timeslot_game_list.append(round_list[ind])
                ind += 1
            # create dictionary entries for formatted game time as string and venue game list
            # format is 12-hour hour:minutes
            timeslot_obj[start_time_key_CONST] = gametime.strftime('%I:%M')
            timeslot_obj[venue_game_list_key_CONST] = timeslot_game_list
            gametime += game_interval
            single_game_cycle_list.append(timeslot_obj)
        if (num_in_last_slot):
            timeslot_obj = {}
            timeslot_game_list = []
            for v in range(num_in_last_slot):
                timeslot_game_list.append(round_list[ind])
                ind += 1
            timeslot_obj[start_time_key_CONST] = gametime.strftime('%I:%M')
            timeslot_obj[venue_game_list_key_CONST] = timeslot_game_list
            single_game_cycle_list.append(timeslot_obj)

        total_round_list.append(single_game_cycle_list)

    print "total round list=",total_round_list, "len=",len(total_round_list)
    return total_round_list
