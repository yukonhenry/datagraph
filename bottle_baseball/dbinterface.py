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

    def findDivisionSchedule(self,age, gender, numgames):
        game_list = []
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
        return game_list

    def dropGameCollection(self):
        self.games_col.drop()
