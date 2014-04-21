#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface, DB_Col_Type
import simplejson as json
from collections import namedtuple
import logging
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python
date_format_CONST = '%m/%d/%Y'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')

class SchedDBInterface:
    def __init__(self, mongoClient, schedcol_name):
        self.dbinterface = MongoDBInterface(mongoClient, collection_name=schedcol_name, db_col_type=DB_Col_Type.GeneratedSchedule)
        self.schedcol_name = schedcol_name

    def setschedule_param(self,db_type, divcol_name, fieldcol_name):
        query_obj = {'divdb_type':{"$exists":True}}
        document = {'divdb_type':db_type, 'divcol_name':divcol_name,
            'fieldcol_name':fieldcol_name}
        docID = self.dbinterface.updatedoc(query_obj, document, upsert=True)

    def getschedule_param(self):
        query_obj = {'divdb_type':{"$exists":True}}
        document = self.dbinterface.getdoc(query_obj, findone_flag=True)
        #game_list = [{k.lower():v for k,v in x.items()} for x in game_list]
        #return self.dbinterface.getdoc(query_obj, findone_flag=True)

    def insertGameData(self, age, gen, fieldday_id, game_date, start_time, venue, home, away):
        document = {'DIV_AGE':age, 'DIV_GEN':gen, 'FIELDDAY_ID':fieldday_id,
                    'GAME_DATE':game_date,
                    'START_TIME':start_time,
                    'GAME_DATE_ORD':game_date.toordinal(),
                    'VENUE':venue, 'HOME':home, 'AWAY':away}
        docID = self.dbinterface.insertdoc(document)

    def updatesched_status(self):
        self.dbinterface.setSchedStatus_col()

    def getsched_status(self):
        return self.dbinterface.getSchedStatus()

    def dropcurrent_collection(self):
        self.dbinterface.drop_collection()

    def get_schedule(self, idproperty, div_age='', div_gen='', field_id=0,
        team_id=0):
        if idproperty == 'div_id':
            game_list = self.dbinterface.getdiv_schedule(div_age, div_gen)
            # switch key to lower case for transfer to client
            #game_list = [{k.lower():v for k,v in x.items()}
            #for x in game_list]
        elif idproperty == 'field_id':
            game_list = self.dbinterface.getfield_schedule(field_id)
            # switch key to lower case for transfer to client
            #game_list = [{k.lower():v for k,v in x.items()} for x in game_list]
        elif idproperty == 'team_id':
            game_list = self.dbinterface.getteam_schedule(team_id, div_age, div_gen)
        else:
            game_list = None
        return game_list

