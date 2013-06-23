#!/usr/bin/python
import simplejson as json
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
start_time_CONST = 'START_TIME'
gameday_id_CONST = 'GAMEDAY_ID'
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
        schedule_db.drop_collection('games')
        self.games_col = schedule_db.games

    def insertGameData(self, age, gen, round_id, start_time_str, venue, home, away):
        document = {age_CONST:age, gen_CONST:gen, round_id_CONST:round_id,
                    venue_CONST:venue, home_CONST:home, away_CONST:away}
        docID = self.games_col.insert(document)

    def findDivisionSchedule(age, gender):
        division_data = self.games_col.find({age_CONST:age, gen_CONST:gender})
