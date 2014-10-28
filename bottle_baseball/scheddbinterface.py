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
divdb_type_CONST = 'DIVDB_TYPE'
divcol_name_CONST = 'DIVCOL_NAME'
fieldcol_name_CONST = 'FIELDCOL_NAME'
config_status_CONST = 'CONFIG_STATUS'
# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Status = namedtuple('_List_Status', 'list config_status')

class SchedDBInterface:
    def __init__(self, mongoClient, userid_name, schedcol_name):
        self.dbinterface = MongoDBInterface(mongoClient, userid_name, collection_name=schedcol_name, db_col_type=DB_Col_Type.GeneratedSchedule)
        self.schedcol_name = schedcol_name

    def setschedule_param(self, db_type, divcol_name, fieldcol_name,
        prefcol_name=None, conflictcol_name=None):
        # note config status is always 1 (complete) for newsched because of how
        # UI frontend works
        # config_status is included as dbinterface.getScheduleCollection
        # requires it
        doc = {divdb_type_CONST:db_type, divcol_name_CONST:divcol_name,
            fieldcol_name_CONST:fieldcol_name, 'PREFCOL_NAME':prefcol_name,
            'CONFLICTCOL_NAME':conflictcol_name, config_status_CONST:1}
        docID = self.dbinterface.updateSchedType_doc(doc)

    def getschedule_param(self):
        doc = self.dbinterface.getSchedType_doc({'CONFIG_STATUS':1})
        # delete config status field as not needed by UI for newsched_id
        lc_doc = {k.lower():v for k,v in doc.items()}
        return lc_doc

    def insertGameData(self, age, gen, fieldday_id, game_date, start_time, venue, home, away):
        document = {'DIV_AGE':age, 'DIV_GEN':gen, 'FIELDDAY_ID':fieldday_id,
                    'GAME_DATE':game_date,
                    'START_TIME':start_time,
                    'GAME_DATE_ORD':game_date.toordinal(),
                    'VENUE':venue, 'HOME':home, 'AWAY':away}
        docID = self.dbinterface.insertdoc(document)

    def insertElimGameData(self, age, gen, fieldday_id, game_date, start_time, venue, home, away, match_id, comment, around):
        document = {'DIV_AGE':age, 'DIV_GEN':gen, 'FIELDDAY_ID':fieldday_id,
                    'GAME_DATE':game_date,
                    'START_TIME':start_time,
                    'GAME_DATE_ORD':game_date.toordinal(),
                    'VENUE':venue, 'HOME':home, 'AWAY':away,
                    'MATCH_ID':match_id, 'COMMENT':comment,
                    'AROUND':around}
        docID = self.dbinterface.insertdoc(document)
    def setsched_status(self):
        self.dbinterface.setSchedStatus_col(1)

    def getsched_status(self):
        return self.dbinterface.getSchedStatus()

    def dropgame_docs(self):
        # drop only the game match docs
        self.dbinterface.dropgame_docs()

    def drop_collection(self):
        # drop the whole collection
        self.dbinterface.drop_collection()

    def get_schedule(self, idproperty, div_age='', div_gen='', field_id=0,
        team_id=0, divinfo=None, fieldinfo_tuple=None, elim_flag=False):
        if idproperty == 'div_id' or idproperty == 'tourndiv_id':
            if not elim_flag:
                game_list = self.dbinterface.getdiv_schedule(div_age, div_gen)
            else:
                game_list = self.dbinterface.getelimdiv_schedule(div_age, div_gen)
        elif idproperty == 'field_id':
            game_list = self.dbinterface.getfield_schedule(field_id)
            # switch key to lower case for transfer to client
            #game_list = [{k.lower():v for k,v in x.items()} for x in game_list]
        elif idproperty == 'team_id':
            game_list = self.dbinterface.getteam_schedule(team_id, div_age, div_gen)
        elif idproperty == 'fair_id':
            game_list = self.dbinterface.getfairness_metrics(div_age, div_gen,
                divinfo, fieldinfo_tuple)
        else:
            game_list = None
        return game_list

