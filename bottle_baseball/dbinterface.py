#!/usr/bin/python
''' Copyright YukonTR 2013 '''
import simplejson as json
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
from collections import Counter, namedtuple
from leaguedivprep import getDivID
import logging
import socket
start_time_CONST = 'START_TIME'
gameday_id_CONST = 'GAMEDAY_ID'
gameday_data_CONST = 'GAMEDAY_DATA'
bye_CONST = 'BYE'  # to designate teams that have a bye for the game cycle
home_CONST = 'HOME'
away_CONST = 'AWAY'
venue_count_CONST = 'VCNT'
home_index_CONST = 0
away_index_CONST = 1
round_id_CONST = 'ROUND_ID'
game_team_CONST = 'GAME_TEAM'
venue_CONST = 'VENUE'
age_CONST = 'AGE'
gen_CONST = 'GEN'
homeratio_CONST = 'HOMERATIO'
team_id_CONST = 'TEAM_ID'
totalgames_CONST = 'TOTALGAMES'
venue_count_CONST = 'VENUE_COUNT'
venue_count_list_CONST = 'VENUE_COUNT_LIST'
sched_status_CONST = 'SCHED_STATUS'

class MongoDBInterface:
    def __init__(self):
        if socket.gethostname() == 'web380.webfaction.com':
            client = MongoClient('localhost', 11466)
        else:
            client = MongoClient()
        self.schedule_db = client.schedule_db
        self.games_col = self.schedule_db.games
        if not self.games_col.find_one({sched_status_CONST:{"$exists":True}}):
            self.games_col.insert({sched_status_CONST:0})

    def insertGameData(self, age, gen, gameday_id, start_time_str, venue, home, away):
        document = {age_CONST:age, gen_CONST:gen, gameday_id_CONST:gameday_id,
                    start_time_CONST:start_time_str,
                    venue_CONST:venue, home_CONST:home, away_CONST:away}
        docID = self.games_col.insert(document)

    def updateGameTime(self, venue, gameday_id, old_start_time, new_start_time):
        query = {gameday_id_CONST:gameday_id, venue_CONST:venue,
                 start_time_CONST:old_start_time}
        updatefields = {"$set":{start_time_CONST:new_start_time}}
        logging.debug("dbinterface:updateGameTime: query=%s, update=%s", query, updatefields)
        docID = self.games_col.update(query, updatefields)


    def findDivisionSchedule(self,age, gender):
        # use mongodb aggregation framework to group results by shared gametime.
        # query for all rounds at once - alternate way is to loop query based
        # on round id/gameday id (knowing total number of games in season)
        # but that potentially does not work if a division ends up not having
        # any games on a particular game day.

        # ref docs.mongodb.org/manual/reference/aggregation/
        # http://stackoverflow.com/questions/14770170/how-to-find-mongo-documents-with-a-same-field
        # also see aggregatin 'mongodb definitive guide'
        # col.aggregate({$match:{AGE:'U12',GEN:'B'}}, {$group:{_id:{GAMEDAY_ID:'$GAMEDAY_ID',START_TIME:"$START_TIME"},count:{$sum:1},docs:{$push:{HOME:'$HOME',AWAY:'$AWAY',VENUE:'$VENUE'}}}},{$sort:{'_id.GAMEDAY_ID':1,'_id.START_TIME':1}})
        result_list = self.games_col.aggregate([{"$match":{age_CONST:age,gen_CONST:gender}},
                                                 {"$group":{'_id':{gameday_id_CONST:"$GAMEDAY_ID",
                                                                   start_time_CONST:"$START_TIME"},
                                                            'count':{"$sum":1},
                                                            gameday_data_CONST:{"$push":{home_CONST:"$HOME",
                                                                                         away_CONST:"$AWAY",
                                                                                         venue_CONST:"$VENUE"}}
                                                            }},
                                                {"$sort":{'_id.GAMEDAY_ID':1, '_id.START_TIME':1}}])
        game_list = []
        for result in result_list['result']:
            #print 'result',result
            sortkeys = result['_id']
            gameday_id = sortkeys[gameday_id_CONST]
            start_time = sortkeys[start_time_CONST]
            gameday_data = result[gameday_data_CONST]
            game_list.append({gameday_id_CONST:gameday_id, start_time_CONST:start_time,
                              gameday_data_CONST:gameday_data})
        #pdb.set_trace()
        return game_list

    def findDivisionSchedulePHMSARefFormat(self):
        ''' query for all games, but sort according to date, time, division '''
        game_curs = self.games_col.find({},{'_id':0})
        game_curs.sort([(gameday_id_CONST,1),(start_time_CONST,1), (age_CONST,1), (gen_CONST,1), (venue_CONST,1)])
        schedule_list = []
        for game in game_curs:
            schedule_list.append({gameday_id_CONST:game[gameday_id_CONST],
                                  start_time_CONST:game[start_time_CONST],
                                  age_CONST:game[age_CONST],
                                  gen_CONST:game[gen_CONST],
                                  home_CONST:game[home_CONST],
                                  away_CONST:game[away_CONST],
                                  venue_CONST:game[venue_CONST]})
        return schedule_list

    def findTeamSchedule(self, age, gender, team_id):
        team_game_curs = self.games_col.find({age_CONST:age, gen_CONST:gender,
                                            "$or":[{home_CONST:team_id},{away_CONST:team_id}]},
                                            {'_id':0, age_CONST:0, gen_CONST:0})
        team_game_curs.sort([(gameday_id_CONST,1),(start_time_CONST,1)])
        team_game_list = []
        for team_game in team_game_curs:
            team_game_list.append({gameday_id_CONST:team_game[gameday_id_CONST],
                                   start_time_CONST:team_game[start_time_CONST],
                                   venue_CONST:team_game[venue_CONST],
                                   home_CONST:team_game[home_CONST],
                                   away_CONST:team_game[away_CONST]})
        return team_game_list

    def findFieldSchedule(self, venue_id):
        field_game_curs = self.games_col.find({venue_CONST:venue_id},
                                              {'_id':0, venue_CONST:0})
        field_game_curs.sort([(gameday_id_CONST,1),(start_time_CONST,1)])
        field_game_list = []
        for field_game in field_game_curs:
            field_game_list.append({gameday_id_CONST:field_game[gameday_id_CONST],
                                    start_time_CONST:field_game[start_time_CONST],
                                    age_CONST:field_game[age_CONST],
                                    gen_CONST:field_game[gen_CONST],
                                    home_CONST:field_game[home_CONST],
                                    away_CONST:field_game[away_CONST]})
        return field_game_list

    def getTimeSlotMetrics(self, age, gender, fields, numgamesperseason):
        # find max min start time for each gameday/field and provide summary stats for how many earliest/latest games each team has
        # ref http://stackoverflow.com/questions/15334408/find-distinct-documents-with-max-value-of-a-field-in-mongodb
        #col.aggregate({$match:{AGE:'U10',GEN:'B',GAMEDAY_ID:1}},{$group:{_id:"$START_TIME",samestart:{$push:{HOME:"$HOME",AWAY:"$AWAY"}}}},{$sort:{_id:-1}},{$group:{_id:0,max:{$first:{samestart:"$samestart"}},min:{$last:{samestart:"$samestart"}}}})
        #### bug with above aggregate query - above query gets the metrics for earliest / latest games in each division,
        # but what we want is the metrics for each division, but earliest/latest is defined as the earliest/latest in Each Field
        # i.e. with the buggy version we counted earliest games if it was the earliest game for that division, but there could have
        # been an earlier game on the same field, but played by teams from a different division.  We count it only if it is the
        # very first (or last) game in the field
        # aggregate both fields at once; pipeline will give results for each field (and robust against situations where first/last
        # games might be different for each field)
        # col.aggregate({$match:{GAMEDAY_ID:1, VENUE:{$in:[1,2]}}},{$group:{_id:{starttime:"$START_TIME",venue:"$VENUE"}, samestart:{$push:{HOME:"$HOME", AWAY:"$AWAY",VENUE:"$VENUE", GEN:"$GEN"}}}},{$sort:{"_id.starttime":-1}},{$group:{_id:"$_id.venue",max:{$first:{samestart:"$samestart",time:"$_id.starttime"}},min:{$last:{samestart:"$samestart",time:"$_id.starttime"}}}})
        ############ if we want to take away the gameday_id for loop below:
        # col.aggregate({$match:{VENUE:{$in:[1,2]}}},{$group:{_id:{starttime:"$START_TIME",venue:"$VENUE", gameday_id:"$GAMEDAY_ID"}, samestart:{$push:{HOME:"$HOME", AWAY:"$AWAY",VENUE:"$VENUE", GEN:"$GEN"}}}},{$sort:{"_id.starttime":-1}},{$group:{_id:{venue:"$_id.venue",gameday_id:"$_id.gameday_id"},max:{$first:{samestart:"$samestart",time:"$_id.starttime"}},min:{$last:{samestart:"$samestart",time:"$_id.starttime"}}}})
        latest_teams = []
        earliest_teams = []
        for gameday_id in range(1,numgamesperseason+1):
            # note for now we will do a query for each gameday_id - issue is that for each gameday, the earliest (less likely)
            # and latest (more likely) game times may change, complicating aggregation $first and $last aggregation queries
            # if we decide to do one single aggreagation pipeline
            # ref http://docs.mongodb.org/manual/tutorial/aggregation-examples/  <--- read and understand
            # OLD, Buggy: pipeline description: match on age,gender,gamday_id; group results based on start_time; then sort (descending);
            # take first and last entries to correspond with earliest and latest times
            # elements consist of home and away team lists that can be concatenated later to make a generic team list
            # NEW: pipeline description: match on field and gameday_id, group results based on starttime and venue, while defining
            # group to consist of teams (home and away), agegroup; sort based on starttime; group sorted results based on field
            # and define group output based on earliest and latest of prev sort operation (but for every field);
            # and carry along latest group operation output with team info, along with time
            res_list = self.games_col.aggregate([{"$match":{venue_CONST:{"$in":fields},
                                                           gameday_id_CONST:gameday_id}},
                                                 {"$group":{'_id':{'start_time':"$START_TIME",
                                                                   'venue':"$VENUE"},
                                                            'data':{"$push":{'home':"$HOME",
                                                                             'away':"$AWAY",
                                                                             'gen':"$GEN",
                                                                             'age':"$AGE"}}}},
                                                 {"$sort":{'_id.start_time':1}},
                                                 {"$group":{'_id':"$_id.venue",
                                                            'earliest':{"$first":{'data':"$data",
                                                                                'time':"$_id.start_time"}},
                                                            'latest':{"$last":{'data':"$data",
                                                                               'time':"$_id.start_time"}}}},
                                                 {"$project":{'_id':0, 'venue':"$_id",
                                                              'earliest':1,'latest':1}}])
            '''
            res_list = self.games_col.aggregate([{"$match":{age_CONST:age, gen_CONST:gender,
                                                            gameday_id_CONST:gameday_id}},
                                                 {"$group":{'_id':"$START_TIME",
                                                            'hometeam_id_list':{"$push":"$HOME"},
                                                            'awayteam_id_list':{"$push":"$AWAY"}}},
                                                 {"$sort":{'_id':-1}},
                                                 {"$group":{'_id':0,
                                                            'latest_data':{"$first":{'hometeam_id_list':"$hometeam_id_list",
                                                                                     'awayteam_id_list':"$awayteam_id_list",
                                                                                     'time':"$_id"}},
                                                            'earliest_data':{"$last":{'hometeam_id_list':"$hometeam_id_list",
                                                                                      'awayteam_id_list':"$awayteam_id_list",
                                                                                      'time':"$_id"}}}},
                                                 {"$project":{'_id':0,'latest_data':1,'earliest_data':1}}])
        '''
            result = res_list['result'] # there should only be one element which includes the latest and earliest team data
            earliest_home = [x['earliest']['data'][0]['home']
                             for x in result
                             if x['earliest']['data'][0]['age']==age and x['earliest']['data'][0]['gen']==gender]
            earliest_away = [x['earliest']['data'][0]['away']
                             for x in result
                             if x['earliest']['data'][0]['age']==age and x['earliest']['data'][0]['gen']==gender]
            latest_home = [x['latest']['data'][0]['home']
                           for x in result
                           if x['latest']['data'][0]['age']==age and x['latest']['data'][0]['gen']==gender]
            latest_away = [x['latest']['data'][0]['away']
                           for x in result
                           if x['latest']['data'][0]['age']==age and x['latest']['data'][0]['gen']==gender]
            logging.debug("dbinterface:getMetrics:query result=%s earliest home=%s earliest away=%s",
                          result, earliest_home, earliest_away)
            logging.debug("dbinterface:getMetrics: latest home=%s latest away=%s",
                          latest_home, latest_away)
            earliest_teams += earliest_home + earliest_away
            latest_teams += latest_home + latest_away
        # ref http://stackoverflow.com/questions/2600191/how-to-count-the-occurrences-of-a-list-item-in-python
        latest_counter_dict = Counter(latest_teams)
        earliest_counter_dict = Counter(earliest_teams)
        logging.debug("dbinterface:getMetrics div=%s%s earliest_teams=%s, earliest_counter_dict=%s",
                      age, gender, earliest_teams, earliest_counter_dict)
        logging.debug("dbinterface:getMetrics latest_teams=%s, latest_counter_dict=%s",
                      latest_teams, latest_counter_dict)
        EL_counter = namedtuple('EL_counter','earliest latest')
        return EL_counter(earliest_counter_dict, latest_counter_dict)

    def getMetrics(self, age, gender, divisionData):
        numTeams = divisionData['totalteams']
        fields = divisionData['fields']
        numgamesperseason = divisionData['gamesperseason']
        ELcounter_tuple = self.getTimeSlotMetrics(age, gender, fields, numgamesperseason)
        earliest_counter_dict = ELcounter_tuple.earliest
        latest_counter_dict = ELcounter_tuple.latest
        metrics_list = []
        for team_id in range(1, numTeams+1):
            numGames = self.games_col.find({age_CONST:age,gen_CONST:gender,
                                            "$or":[{home_CONST:team_id},{away_CONST:team_id}]
                                            }).count()
            numHomeGames = self.games_col.find({age_CONST:age,gen_CONST:gender,home_CONST:team_id}).count()
            homeratio = float(numHomeGames)/float(numGames)
            field_count_list = []
            for venue in fields:
                venue_count = self.games_col.find({age_CONST:age,gen_CONST:gender,venue_CONST:venue,
                                                   "$or":[{home_CONST:team_id},{away_CONST:team_id}]
                                                   }).count()
                field_count_list.append({venue_CONST:venue, venue_count_CONST:venue_count})

            metrics_list.append({team_id_CONST:team_id, totalgames_CONST:numGames,
                                 homeratio_CONST:homeratio,
                                 venue_count_list_CONST:field_count_list,
                                 'EARLIEST_COUNT':earliest_counter_dict[team_id],
                                 'LATEST_COUNT':latest_counter_dict[team_id]})
        return metrics_list


    def dropGameCollection(self):
        self.games_col.drop()
        self.resetSchedStatus_col()

    def resetSchedStatus_col(self):
        # add upsert as when resetSchedStatus is called by dropGameCollection, games collection was just wiped out.
        self.games_col.update({sched_status_CONST:{"$exists":True}},
                              {"$set":{sched_status_CONST:0}}, upsert=True)

    def setSchedStatus_col(self):
        self.games_col.update({sched_status_CONST:{"$exists":True}},
                              {"$set":{sched_status_CONST:1}})

    def getSchedStatus(self):
        return self.games_col.find_one({sched_status_CONST:{"$exists":True}})[sched_status_CONST]

    def getScheduleCollections(self):
        # ref http://api.mongodb.org/python/current/api/pymongo/database.html
        sc_list = self.schedule_db.collection_names(include_system_collections=False)
        # check for size of collection because if size is one, it only includes the SCHED_STATUS doc
        schedcollect_list = [x for x in sc_list if self.schedule_db[x].count() > 1]
        return schedcollect_list
