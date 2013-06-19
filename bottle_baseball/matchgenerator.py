bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
homeaway_CONST = 'HOMEAWAY'
home_CONST = 'HOME'
away_CONST = 'AWAY'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
#http://www.tutorialspoint.com/python/python_classes_objects.htm
class MatchGenerator:
    def __init__(self, nt, ng):
        self.numTeams = nt
        self.numGames = ng  # number games per team per season
        self.bye_flag = False
        if (self.numTeams % 2):
            self.eff_numTeams = self.numTeams+1
            self.bye_flag = True
        else:
            self.eff_numTeams = self.numTeams
            self.bye_flag = False
        # half_n, num_time_slots, num_in_last_slot are variables relevant for schedule making
        # within a game day
        # half_n denotes number of positions on the scheduling circle, so it is independent
        # whether there is a bye or not
        self.half_n = self.eff_numTeams/2
        self.timeslots_per_day = 0

        #self.games_by_round_list = []
        self.metrics_list = []
        for i in range(nt):
            # dictionary key is team id, which is 1-based
            # can't use tuple because tuple does not support assignment
            # try array here
            # _id key added, but check if properly used later
            self.metrics_list.append({'_id':i+1, # id is one-based
                                      homeaway_CONST:[0,0]})

    def generateCirclePairing(self, circle_total_pos, circlecenter_team, game_count, match_by_round_list):
        for rotation_ind in range(circle_total_pos):
            if game_count >= self.numGames:
                break
            else:
                game_count += 1
                # each rotation_ind corresponds to a single game cycle (a week if there is one game per week)
            circletop_team = rotation_ind + 1   # top of circle
            # first game pairing
            if (not self.bye_flag):
                round_list = [{home_CONST:circletop_team, away_CONST:circlecenter_team}]
                # increment home-away counters (team-id, 1-based)
                self.metrics_list[circletop_team-1][homeaway_CONST][home_index_CONST] += 1
                self.metrics_list[circlecenter_team-1][homeaway_CONST][away_index_CONST] += 1
            else:
                round_list = []
            for j in range(1, self.half_n):
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

                self.metrics_list[CCW_team-1][homeaway_CONST][home_index_CONST] += 1
                self.metrics_list[CW_team-1][homeaway_CONST][away_index_CONST] += 1
                round_list.append({home_CONST:CCW_team, away_CONST:CW_team})
            # round id is 1-index based, equivalent to team# at top of circle
            match_by_round_list.append({round_id_CONST:game_count, game_team_CONST:round_list})
        return game_count

    def generateMatchList(self):

        '''
        Implement circle method.  Circle iterates from 0 to one less than
        total number of effective teams.  Virtual team used if there is a bye.
        Outer loop emulates circle rotation (CCW)
        http://en.wikipedia.org/wiki/Round-robin_tournament
        http://mat.tepper.cmu.edu/trick/banff.ppt
        '''
        # define center (of circle) team - this will be fixed
        if (not self.bye_flag):
            circlecenter_team = self.eff_numTeams
        else:
            circlecenter_team = 0

        # outer loop emulates circle rotation there will be eff_numTeams-1 iterations
        # corresponds to number of game rotations, i.e. weeks (assuming there is one week per game)
        circle_total_pos = self.eff_numTeams - 1
        match_by_round_list = []
        game_count = 0
        while (game_count < self.numGames):
            game_count = self.generateCirclePairing(circle_total_pos, circlecenter_team, game_count, match_by_round_list)
        return match_by_round_list


