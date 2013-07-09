from itertools import product
import networkx as nx
from math import sqrt
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
home_CONST = 'HOME'
away_CONST = 'AWAY'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
large_CONST = 1e7
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
        self.matchG = nx.DiGraph()

    def removeGraphEdgeAttribute(self, source_id, sink_id, gamecount_id):
        # delete edge from matchG graph
        edge_dict = self.matchG.get_edge_data(source_id, sink_id, default=None)
        if (edge_dict):
            gamecount_id_list = edge_dict['gamecount_id']
            if len(gamecount_id_list) <= 1:
                # this is the only match with the home away game, remove edge
                self.matchG.remove_edge(source_id, sink_id)
            else:
                # there are two or more games with this homeaway match,
                # remove only relevant attrib entry
                gamecount_id_list.remove(gamecount_id)
                # re-insert attribute list (based on original home away team id's)
                self.matchG.edge[source_id][sink_id]['gamecount_id'] = gamecount_id_list
            return True
        else:
            return False

    def addGraphEdgeAttribute(self, source_id, sink_id, gamecount_id):
        if not self.matchG.has_edge(source_id, sink_id):
            # check if directed edge already exists, then if not
            self.matchG.add_edge(source_id, sink_id, gamecount_id=[gamecount_id])
        else:
            # if directed edge already exists
            self.matchG[source_id][sink_id]['gamecount_id'].append(gamecount_id)

    def getBalancedHomeAwayTeams(self, team1_id, team2_id, gamecount_id):
        # assign home away teams based on current home game counters for the two teams
        # team id's are 1-indexed so decrement to get 0-index-based list position
        t1_ind = team1_id - 1
        t2_ind = team2_id - 1
        if (self.metrics_list[t1_ind] <= self.metrics_list[t2_ind]):
            # if team1 should be the home team
            gamematch = {home_CONST:team1_id, away_CONST:team2_id}
            self.addGraphEdgeAttribute(team1_id, team2_id, gamecount_id)
            self.metrics_list[t1_ind] += 1
        else:
            # team2 should be the home team
            gamematch = {home_CONST:team2_id, away_CONST:team1_id}
            self.addGraphEdgeAttribute(team2_id, team1_id, gamecount_id)
            self.metrics_list[t2_ind] += 1
        return gamematch

    # calculate cost function - euclidean distance between metrics_list and
    # targethome_count_list (if targethome_count is a list itself, then distance is defined
    # as the minimum distance to that list (closest element)
    # prototype for calculating list of absoute value differences (before calculating sqrt of sum sq)
    # list1 = []
    # for (a1,b1) in zip(a,b):
	#    list2 = []
    #    for b2 in b1:
    #	    list2.append(abs(a1-b2) if a1 not in b1 else 0)
	#    list1.append(min(list2))
    def computeCostFunction(self, metrics_list):
        absdiff_list = [min([abs(m-t2) if m not in t else 0 for t2 in t]) for (m,t) in zip(metrics_list, self.targethome_count_list)]
        euclidean_norm = sqrt(sum([x*x for x in absdiff_list]))
        return euclidean_norm

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
            round_id = match_by_round[round_id_CONST]
            max_team_id = max_ind + 1
            min_team_id = min_ind + 1
            try:
                # note match_ind is just the position in the round_list, and not the
                # round_id/game_count_id
                match_ind = round_list.index({home_CONST:max_team_id, away_CONST:min_team_id})
            except ValueError:
                # if index is not found
                continue
            else:
                print '===='
                print 'matchG edge list attributes before swap',nx.get_edge_attributes(self.matchG,'gamecount_id')
                # first delete edge from matchG graph before adding new edge based on swap
                if not removeGraphEdgeAttribute(max_team_id, min_team_id, round_id):
                    print 'Possible Error: Not able to remove graph edge between', max_team_id, min_team_id, round_id
                # do swap
                round_list[match_ind] = {home_CONST:min_team_id, away_CONST:max_team_id}
                self.metrics_list[max_ind] -= 1
                self.metrics_list[min_ind] += 1
                # add swapped edge to directed graph
                self.addGraphEdgeAttribute(min_team_id, max_team_id, round_id)
                print '--------------------'
                print 'home away SWAPPED', min_team_id, max_team_id
                print 'new metrics list', self.metrics_list
                print 'targethome',self.targethome_count_list
                print 'matchG edge list attributes AFTER swap',nx.get_edge_attributes(self.matchG,'gamecount_id')
                #pdb.set_trace()
                foundFlag = True
                break;
        else:
            gamecount_id_attrib = nx.get_edge_attributes(self.matchG,'gamecount_id')
            current_cost = self.computeCostFunction(self.metrics_list)
            bestcost = large_CONST  # specify a very large number
            print '+++++No simple pair to swap found, going to search for multiple edges++++++++++++++++++'
            print 'current cost for self metrics =',self.metrics_list, current_cost
            for (max_ind, min_ind) in product(maxdiff_ind_list, mindiff_ind_list):
                max_team_id = max_ind+1
                min_team_id = min_ind+1
                if nx.has_path(self.matchG, max_team_id, min_team_id):
                    print 'OK there is some path between', max_team_id, min_team_id
                    paths_gen = nx.all_shortest_paths(self.matchG, max_team_id, min_team_id)
                    for path in paths_gen:
                        # for each path, we are going to emulate how cost function
                        # would change if home and away teams were swapped
                        # note that the path itself begins with the home team
                        # in the directed graph, but after the emulated swap, the
                        # first team_id in the path is the away team
                        # i.e.  if path is [10,5,8] which is H-A 10-5, H-A 5-8
                        # after the swap H-A 8-5, H-A 5-10
                        # we won't be doing the actual swap, but for metrics calculation
                        # the away team is considered the 'new' home team.
                        tempmetrics_list = list(self.metrics_list)
                        print 'Path=',path
                        path_it = iter(path)
                        away_id = next(path_it, 0)
                        temporig_list = []
                        tempswapped_list = []
                        while True:
                            home_id = away_id
                            away_id = next(path_it,0)
                            if away_id == 0:
                                break
                            else:
                                # do emulated swap and adjust metrics
                                tempmetrics_list[home_id-1] -= 1
                                tempmetrics_list[away_id-1] += 1
                                temporig_list.append({home_CONST:home_id,
                                                      away_CONST:away_id})
                                # keep track of swapped teams
                                tempswapped_list.append({home_CONST:away_id,
                                                         away_CONST:home_id})
                        tempcost = self.computeCostFunction(tempmetrics_list)
                        print 'temp metrics and cost w list', tempmetrics_list, tempcost,tempswapped_list
                        if tempcost < bestcost:
                            bestcost = tempcost
                            bestorig_list = temporig_list
                            bestswapped_list = tempswapped_list
                    print 'best path for teams, cost', max_team_id, min_team_id, bestswapped_list, bestcost
                    foundFlag = True
                else:
                    print 'no path between', max_team_id, min_team_id
                    foundFlag = False
            if foundFlag:
                print '@@@@'
                print 'best path found between', max_team_id, min_team_id, bestswapped_list
                for edgematch in bestorig_list:
                    if not removeGraphEdgeAttribute(edgematch[home_CONST],
                                                    edgematch[away_CONST],
                                                    round_id):
                    print 'Possible Error(2): Not able to remove graph edge between', max_team_id, min_team_id

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
            print 'attempt:', matchcounter, ' Even multihop path not found, resorting to heuristics'
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

            count_list = mingames_list + maxgames_list
            self.targethome_count_list = [[c/2] if c%2==0 else [c/2,c/2+1] for c in count_list]
        print 'target home count', self.targethome_count_list

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
                gamematch_dict = self.getBalancedHomeAwayTeams(circletop_team, circlecenter_team,
                                                               game_count)
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
                gamematch_dict = self.getBalancedHomeAwayTeams(CCW_team, CW_team, game_count)
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
