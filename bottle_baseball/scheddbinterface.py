#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
import logging

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')

class SchedDBInterface:
    def __init__(self, mongoClient, schedcol_name):
        self.dbinterface = MongoDBInterface(mongoClient, collection_name=schedcol_name, db_col_type=DB_Col_Type.GeneratedSchedule)
        self.schedcol_name = schedcol_name

    def insertGameData(self, age, gen, fieldday_id, game_date_str, start_time_str, venue, home, away):
        document = {'DIV_AGE':age, 'DIV_GEN':gen, 'FIELDDAY_ID':fieldday_id,
                    'GAME_DATE':game_date_str, 'START_TIME':start_time_str,
                    'VENUE':venue, 'HOME':home, 'AWAY':away}
        docID = self.dbinterface.insertdoc(document)

    def updatesched_status(self):
        self.dbinterface.setSchedStatus_col()

    def getsched_status(self):
        return self.dbinterface.getSchedStatus()

    def dropcurrent_collection(self):
        self.dbinterface.drop_collection()

    def get_schedule(self, idproperty, age='', gender='', field_id=0):
        if idproperty == 'div_id':
            game_list = self.dbinterface.getdiv_schedule(age, gender)
            # switch key to lower case for transfer to client
            #game_list = [{k.lower():v for k,v in x.items()}
            #for x in game_list]
            return game_list
        elif idproperty == 'field_id':
            game_list = self.dbinterface.getfield_schedule(field_id)
            # switch key to lower case for transfer to client
            game_list = [{k.lower():v for k,v in x.items()} for x in game_list]
            return game_list
        else:
            return None

