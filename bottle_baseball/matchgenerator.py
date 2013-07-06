from itertools import product
import networkx as nx
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
home_CONST = 'HOME'
away_CONST = 'AWAY'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
#import pdb
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
        # metrics_list is array of counter dictionaries.
        # position in array corresponds to team_id-1 (since team_id is one-index based)
        self.metrics_list = nt*[0]
        self.match_by_round_list = []
        self.targethome_count_list = []
        self.matchG = nx.Graph()

    def getBalancedHomeAwayTeams(self, team1_id, team2_id):
        # assign home away teams based on current home game counters for the two teams
        # team id's are 1-indexed so decrement to get 0-index-based list position
        t1_ind = team1_id - 1
        t2_ind = team2_id - 1
        self.matchG.add_edge(team1_id, team2_id)
        if (self.metrics_list[t1_ind] <= self.metrics_list[t2_ind]):
            gamematch = {home_CONST:team1_id, away_CONST:team2_id}
            self.metrics_list[t1_ind] += 1
        else:
            gamematch = {home_CONST:team2_id, away_CONST:team1_id}
            self.metrics_list[t2_ind] += 1
        return gamematch

    def findMatch(self, diff_list, maxdiff, mindiff):
        # then find indices of team_id that matches the max and min averages
        maxdiff_ind_list = [i for i,j in enumerate(diff_list) if j==maxdiff]
        mindiff_ind_list = [i for i,j in enumerate(diff_list) if j==mindiff]
        print 'max min diff list', maxdiff_ind_list, mindiff_ind_list
        # get all indices that correspond to the max or min home count
        #max_ind_list = [i for i,j in enumerate(self.metrics_list) if j==maxhome_count]
        #min_ind_list = [i for i,j in enumerate(self.metrics_list) if j==minhome_count]
        # ref http://stackoverflow.com/questions/2597104/break-the-nested-double-loop-in-python
        # for breaking out of double loops
        for (match_by_round, max_ind, min_ind) in product(self.match_by_round_list, maxdiff_ind_list, mindiff_ind_list):
            round_list = match_by_round[game_team_CONST]
            max_team_id = max_ind + 1
            min_team_id = min_ind + 1
            try:
                match_ind = round_list.index({home_CONST:max_team_id, away_CONST:min_team_id})
            except ValueError:
                # if index is not found
                continue
            else:
                # do swap
                round_list[match_ind] = {home_CONST:min_team_id, away_CONST:max_team_id}
                self.metrics_list[max_ind] -= 1
                self.metrics_list[min_ind] += 1
                print '--------------------'
                print 'home away SWAPPED', min_team_id, max_team_id
                print 'new metrics list', self.metrics_list
                print 'targethome',self.targethome_count_list
                #pdb.set_trace()
                foundFlag = True
                break;
        else:
            for (max_ind, min_ind) in product(maxdiff_ind_list, mindiff_ind_list):
                max_team_id = max_ind+1
                min_team_id = min_ind+1
                if nx.has_path(self.matchG, max_team_id, min_team_id):
                    print 'OK THERE IS SOME PATH between', max_team_id, min_team_id
                    break
            foundFlag = False
        return foundFlag

    def findandSwap(self):
        # ref for nested list comprehension applicable to below
        # http://stackoverflow.com/questions/3766711/python-advanced-nested-list-comprehension-syntax
        #diff_list = []
        #for (m,t) in zip(self.metrics_list, self.targethome_count_list):
        #    difftemp_list = []
        #    for t2 in t:
        #        difftemp_list.append(abs(m-t2))
        #    diff_list.append(max(difftemp_list))
        #diff_list = [[m-t2 if m not in t else 0 for t2 in t] for (m,t) in zip(self.metrics_list, self.targethome_count_list)]
        # Calculate for each team_id the difference between the home metric and the target home
        # count value.  The target home count value may be a set (represented by a list) if there
        # are an odd number of games for example
        diff_list = [[m-t2 for t2 in t] for (m,t) in zip(self.metrics_list, self.targethome_count_list)]
        # for each team_id determine the average difference betwee metric and target home count
        # average is a reasonable metric especially if the target home count is a set
        avgdiff_list = [sum(elem_list)/float(len(elem_list)) for elem_list in diff_list]
        maxdiff_list = [max(elem_list) for elem_list in diff_list]
        mindiff_list = [min(elem_list) for elem_list in diff_list]
        print 'diff_list, avgdiff_list', diff_list, avgdiff_list

        # find the max and min of average difference
        maxdiff = max(avgdiff_list)
        mindiff = min(avgdiff_list)
        matchcounter = 0
        while not self.findMatch(avgdiff_list, maxdiff, mindiff):
            matchcounter += 1
            print 'attempt:', matchcounter, ' Something may be wrong, max and min teams not found, do it again'
            setavg_list = list(set(avgdiff_list))
            changeMaxFlag = True if abs(maxdiff) < abs(mindiff) else False
            if changeMaxFlag:
                sorted_setavg_list = sorted(setavg_list, reverse=changeMaxFlag)
                # grab second element as the new maxdiff
                maxdiff = sorted_setavg_list[1]
            else:
                sorted_setavg_list = sorted(setavg_list)
                mindiff = sorted_setavg_list[1]

    def adjustHomeAwayTeams(self):
        # make adjustments to the home away assignments by looking at the homeaway counters and looking
        # for gaps
        maxhome_count = max(self.metrics_list)
        minhome_count = min(self.metrics_list)
        print 'max and min homecount', maxhome_count, minhome_count
        count = 1;
        if not self.bye_flag:
            # if there are no bye games for a team, then target number of home game is half the number
            # of total games.
            half_games = self.numGames / 2
            targethome_count = [half_games] if self.numGames%2 == 0 else [half_games, half_games+1]
            self.targethome_count_list = self.numTeams*[targethome_count]
            #self.targethome_count_dict = {id+1:count for (id, count_list) in zip(range(self.numTeams),targethome_count) for count in count_list}
            #self.targethome_count_dict = {id+1:count for id,count_list in enumerate(self.targethome_count_list) for count in count_list }
            # or use enumerate above
        else:
            # the number of bye games per team is either numGameSlots/numTeams (integer div)
            # or one(1) added to the minimum
            # number of teams that have the max number of byes is numGameSlots/numTeams (modulo)
            # otherwise remainder teams have the minimum number of byes
            # each team has either the minNumByes or maxNumByes
            # total games for each team can be computed by the number of game slots
            # minus the min or max number of byes
            minNumByes = self.numGames / self.numTeams
            maxGames = self.numGames - minNumByes
            maxNumByes = minNumByes+1
            minGames = self.numGames - maxNumByes

            numTeams_minGames = self.numGames % self.numTeams
            numTeams_maxGames = self.numTeams - numTeams_minGames

            mingames_list = numTeams_minGames*[minGames]
            maxgames_list = numTeams_maxGames*[maxGames]

            halfMinGames = minGames/2
            halfMaxGames = maxGames/2

            count_list = mingames_list + maxgames_list
            self.targethome_count_list = [[c/2] if c%2==0 else [c/2,c/2+1] for c in count_list]
        print 'target home count', self.targethome_count_list
        #pdb.set_trace()

#        while not all([x in y for (x,y) in zip(self.metrics_list, self.targethome_count_list)]):
        while sum([x in y for (x,y) in zip(self.metrics_list, self.targethome_count_list)]) < self.numTeams-1:
            self.findandSwap()
            maxhome_count = max(self.metrics_list)
            minhome_count = min(self.metrics_list)
            print 'after ', count, 'max and min homecount', maxhome_count, minhome_count
            count += 1
        else:
            print "home and away games already balanced"
            print '----------------------------------------'


    def generateCirclePairing(self, circle_total_pos, circlecenter_team, game_count):
        for rotation_ind in range(circle_total_pos):
            if game_count >= self.numGames:
                break
            else:
                game_count += 1
                # each rotation_ind corresponds to a single game cycle (a week if there is one game per week)
            circletop_team = rotation_ind + 1   # top of circle
            # first game pairing
            if (not self.bye_flag):
                gamematch_dict = self.getBalancedHomeAwayTeams(circletop_team, circlecenter_team)
                round_list = [gamematch_dict]
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
                CCW_team = (((circletop_team-1)-j) % circle_total_pos) + 1
                CW_team = (((circletop_team-1)+j) % circle_total_pos) + 1
                gamematch_dict = self.getBalancedHomeAwayTeams(CCW_team, CW_team)
                round_list.append(gamematch_dict)
            # round id is 1-index based, equivalent to team# at top of circle
            self.match_by_round_list.append({round_id_CONST:game_count, game_team_CONST:round_list})
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
        game_count = 0
        while (game_count < self.numGames):
            game_count = self.generateCirclePairing(circle_total_pos, circlecenter_team, game_count)
        print '****************************************'
        print 'metrics_list', self.numTeams, self.metrics_list
        self.adjustHomeAwayTeams()
        return self.match_by_round_list
