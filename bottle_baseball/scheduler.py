def generateRRSchedule(numTeams, numVenues):
    if (numTeams % 2):
        eff_numTeams = numTeams+1
        bye_flag = True
    else:
        eff_numTeams = numTeams
        bye_flag = False
    half_n = eff_numTeams/2

    ''' not implementing venue number support yet.  Iterate as if
    maximum number of venues were available.
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
    circle_total_pos = eff_numTeams - 1
    total_round_list = []
    for rotation_ind in range(circle_total_pos):
        circletop_team = rotation_ind + 1   # top of circle
        # first game pairing
        round_list = [(circletop_team, circlecenter_team)]
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
        rlist_len = len(round_list)
        num_time_slots = rlist_len / numVenues
        num_in_last_slot = rlist_len % numVenues
        print "numtimeslots, numinlastslot",num_time_slots, num_in_last_slot
        total_round_list.append(round_list)
    return total_round_list
