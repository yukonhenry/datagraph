#!/usr/bin/python
import simplejson as json
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
from collections import Counter
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
venue_count_CONST = 'VENUE_COUNT'
venue_count_list_CONST = 'VENUE_COUNT_LIST'
import pdb
class MongoDBInterface:
    def __init__(self):
        client = MongoClient()
        schedule_db = client.schedule_db
        self.games_col = schedule_db.games

    def insertGameData(self, age, gen, gameday_id, start_time_str, venue, home, away):
        document = {age_CONST:age, gen_CONST:gen, gameday_id_CONST:gameday_id,
                    start_time_CONST:start_time_str,
                    venue_CONST:venue, home_CONST:home, away_CONST:away}
        docID = self.games_col.insert(document)

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

    def getMetrics(self, age, gender, divisionData):
        numTeams = divisionData['totalteams']
        fields = divisionData['fields']
        numGames = divisionData['gamesperseason']
        max_min_start_dict = {}
        # find max min start time for each gameday
        # ref http://stackoverflow.com/questions/15334408/find-distinct-documents-with-max-value-of-a-field-in-mongodb
        #col.aggregate({$match:{AGE:'U10',GEN:'B',GAMEDAY_ID:1}},{$group:{_id:"$START_TIME",samestart:{$push:{HOME:"$HOME",AWAY:"$AWAY"}}}},{$sort:{_id:-1}},{$group:{_id:0,max:{$first:{samestart:"$samestart"}},min:{$last:{samestart:"$samestart"}}}})
        latest_teams = []
        earliest_teams = []
        for gameday_id in range(1,numGames+1):
            # ref http://docs.mongodb.org/manual/tutorial/aggregation-examples/
            # pipeline description: match on age,gender,gamday_id; group results based on start_time; then sort (descending);
            # take first and last entries to correspond with earliest and latest times
            # elements consist of home and away team lists that can be concatenated later to make a generic team list
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
            result = res_list['result'][0] # there should only be one element which includes the latest and earliest team data
            latest_data = result['latest_data']
            earliest_data = result['earliest_data']
            latest_teams += latest_data['hometeam_id_list']+latest_data['awayteam_id_list']
            earliest_teams += earliest_data['hometeam_id_list']+earliest_data['awayteam_id_list']
        # ref http://stackoverflow.com/questions/2600191/how-to-count-the-occurrences-of-a-list-item-in-python
        latest_counter_dict = Counter(latest_teams)
        earliest_counter_dict = Counter(earliest_teams)
        print 'earliest counter',earliest_teams, earliest_counter_dict
        print 'latest counter',latest_teams, latest_counter_dict

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

            metrics_list.append({team_id_CONST:team_id, homeratio_CONST:homeratio,
                                 venue_count_list_CONST:field_count_list,
                                 'EARLIEST_COUNT':earliest_counter_dict[team_id],
                                 'LATEST_COUNT':latest_counter_dict[team_id]})
        return metrics_list


    def dropGameCollection(self):
        self.games_col.drop()
