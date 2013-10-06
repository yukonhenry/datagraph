from dbinterface import MongoDBInterface

class TournamentScheduler:
    def __init__(self, mongoClient, ldtuple, divinfo_col):
        self.leaguedata = ldtuple.dict_list
        self.ldata_indexerGet = ldtuple.indexerGet
        #self.dbinterface = dbinterface

    def generate(self):
        print 'generating cup schedule'
