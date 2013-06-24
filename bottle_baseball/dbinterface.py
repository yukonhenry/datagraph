#!/usr/bin/python
import simplejson as json
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
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
            print 'result',result
            sortkeys = result['_id']
            gameday_id = sortkeys[gameday_id_CONST]
            start_time = sortkeys[start_time_CONST]
            gameday_data = result[gameday_data_CONST]
            game_list.append({gameday_id_CONST:gameday_id, start_time_CONST:start_time,
                              gameday_data_CONST:gameday_data})
        return game_list

        '''
        # second dictionary is a projection operator that removed _id from the returned cursor
        for round_id in range(1, numgames+1):
            gameday_games = self.games_col.find({age_CONST:age, gen_CONST:gender,
                                                 gameday_id_CONST:round_id },
                                                {'_id':0, age_CONST:0, gen_CONST:0, gameday_id_CONST:0})
            print 'gameday games', gameday_games
            times = gameday_games.distinct(start_time_CONST)
            for time in times:
                print 'distinct time', round_id, time
            #print 'distinct',division_games.distinct(gameday_id_CONST)

            gameday_list = []
            for item in gameday_games:
                gameday_list.append(item)
            game_list.append({gameday_id_CONST:round_id, gameday_data_CONST:gameday_list})
        #print 'game_list',game_list
'''

    def dropGameCollection(self):
        self.games_col.drop()
