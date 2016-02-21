#!/usr/bin/python
''' Copyright YukonTR 2013 '''
import simplejson as json
# http://api.mongodb.org/python/current/tutorial.html
from pymongo import  *
from collections import Counter, namedtuple
import logging
import socket
from flufl.enum import Enum
from datetime import date
from pprint import pprint
start_time_CONST = 'START_TIME'
gameday_id_CONST = 'GAMEDAY_ID'
game_date_CONST = 'GAME_DATE'
gameday_data_CONST = 'GAMEDAY_DATA'
home_CONST = 'HOME'
away_CONST = 'AWAY'
venue_CONST = 'VENUE'
age_CONST = 'AGE'
gen_CONST = 'GEN'
team_id_CONST = 'TEAM_ID'
sched_status_CONST = 'SCHED_STATUS'
div_id_CONST = 'DIV_ID'
sched_type_CONST = 'SCHED_TYPE'
match_id_CONST = 'MATCH_ID'
comment_CONST = 'COMMENT'
round_CONST = 'ROUND'
field_id_CONST = 'FIELD_ID'
CONFIG_STATUS = 'CONFIG_STATUS'
divstr_colname_CONST = 'DIVSTR_COLNAME'
DIVSTR_DB_TYPE = 'DIVSTR_DB_TYPE'
fieldday_id_CONST = 'FIELDDAY_ID'
div_age_CONST = 'DIV_AGE'
div_gen_CONST = 'DIV_GEN'
USER_ID = 'USER_ID'
ODDNUM_MODE = 'ODDNUM_MODE'
SCHED_CAT = 'SCHED_CAT'

# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
# http://stackoverflow.com/questions/10624937/convert-datetime-object-to-a-string-of-date-only-in-python
date_format_CONST = '%m/%d/%Y'

# global for namedtuple
_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')
_List_Result = namedtuple('_List_Result', 'list result')
_PlusList_Status = namedtuple('_PlusList_Status', 'list config_status divstr_colname divstr_db_type')

# http://pythonhosted.org/flufl.enum/docs/using.html
class DB_Col_Type(Enum):
    RoundRobin = 1
    TournRR = 2
    FieldInfo = 3
    GeneratedSchedule = 4
    PreferenceInfo = 5
    TeamInfo = 6
    ConflictInfo = 7
    UserInfo = 8
    ElimTourn = 9

class MongoDBInterface:
    def __init__(self, mongoClient, userid_name=None, collection_name=None,
        sched_cat="L", db_col_type=DB_Col_Type.RoundRobin):
        # default db name is schedule_db
        self.schedule_db = mongoClient.schedule_db
        if collection_name and userid_name:
            self.collection = self.schedule_db[collection_name]
            self.userid_name = userid_name
            # fyi sched_type with str(db_col_type) is important as without str
            # encapsulation there is a runtime encode error
            self.sched_type = str(db_col_type)
            # schedule category is represented by "L", or "T" - denoting League
            # or Tournament scheduling
            self.sched_cat = sched_cat
            if not self.collection.find_one({sched_status_CONST:{"$exists":True},
                sched_type_CONST:self.sched_type, USER_ID:userid_name,
                SCHED_CAT:sched_cat}):
                self.collection.insert({sched_status_CONST:0,
                    sched_type_CONST:self.sched_type, USER_ID:userid_name,
                    SCHED_CAT:sched_cat})

    def insertdoc(self, document):
        document.update({'SCHED_TYPE':self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat})
        docID = self.collection.insert_one(document)
        return docID

    def updatedoc(self, query_obj, operator, operator_obj, upsert_flag=False):
        ''' Update single element of an array subdocument
        ref http://mongoblog.tumblr.com/post/21792332279/updating-one-element-in-an-array
        http://www.developingandstuff.com/2013/12/modify-element-of-array-in-mongodb.html
        ensure we are only adding to the same exact sched_type
        '''
        query_obj.update({'SCHED_TYPE':self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat})
        result_obj = self.collection.update(query_obj, {operator:operator_obj},
            upsert=upsert_flag)
        if 'writeConcernError' in result_obj:
            raise CodeLogicError("dbinterface:updatedoc: collection update error=%s" %(result_obj.writeConcernError.errmsg,))
            return -1
        else:
            return 1

    def check_docexists(self, key):
        # use key to check if doc exists - return boolean
        # Note an empty result still produces a cursor object to be returned from
        # the find().limit(1) statement, which makes the if .. check always
        # succeed regardless if there is a result or not.
        # To make the test a correct one, append with .count() statement to make
        # sure the cursor result contains an element
        if self.collection.find({"SCHED_TYPE":self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat,
            key:{"$exists":True}}, {key:1}).limit(1).count() > 0:
            return True
        else:
            return False

    def getdoc(self, query_obj, projection_obj, findone_flag=False):
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        # use limit(1) instead based on recommendation above rather than find_one
        if findone_flag:
            return self.collection.find(query_obj, projection_obj).limit(1)
        else:
            return self.collection.find(query_obj, projection_obj)

    def insertGameData(self, age, gen, gameday_id, start_time_str, venue, home, away):
        document = {age_CONST:age, gen_CONST:gen, gameday_id_CONST:gameday_id,
                    start_time_CONST:start_time_str,
                    venue_CONST:venue, home_CONST:home, away_CONST:away}
        docID = self.collection.insert(document)

    def updateInfoDocument(self, doc_list, set_obj, id_str):
        # note $set operator only updates specified fields, not the entire document
        # change doc structure to be similar to the fielddb structure - separate
        # doc for each div_id, instead of putting it all as subdocuments under
        # DOC_LIST
        self.collection.update({sched_type_CONST:self.sched_type,
            sched_status_CONST:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {"$set": set_obj}, upsert=True)
        # remove existing config documents for the same doc type and id
        self.collection.remove({sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat,
            id_str:{"$exists":True}})
        for doc in doc_list:
            # put fieldinfo in separate mongo documents
            # each doc should have a sched_type field
            doc[sched_type_CONST] = self.sched_type
            doc[USER_ID] = self.userid_name
            doc[SCHED_CAT] = self.sched_cat
            self.collection.update({sched_type_CONST:self.sched_type,
                id_str:doc[id_str], USER_ID:self.userid_name,
                SCHED_CAT:self.sched_cat}, doc, upsert=True)


    def updateSchedType_doc(self, updatedoc):
        result_obj = self.collection.update({
            sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat},
            {"$set": updatedoc}, upsert=True)

    def updateInfoPlusDocument(self, doc_list, config_status, divstr_colname, divstr_db_type, id_str):
        # going to flatten doc structure for fields - do away with doc_list top
        # level structure; put divstr information into main status doc
        self.collection.update({sched_type_CONST:self.sched_type,
            sched_status_CONST:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {"$set": {CONFIG_STATUS:config_status,
            divstr_colname_CONST:divstr_colname,
            DIVSTR_DB_TYPE:divstr_db_type}}, upsert=True)
        self.collection.remove({sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat,
            id_str:{"$exists":True}})
        for doc in doc_list:
            # put fieldinfo in separate mongo documents
            # each doc should have a sched_type field
            doc[sched_type_CONST] = self.sched_type
            doc[USER_ID] = self.userid_name
            doc[SCHED_CAT] = self.sched_cat
            self.collection.update({sched_type_CONST:self.sched_type,
                id_str:doc[id_str], USER_ID:self.userid_name,
                SCHED_CAT:self.sched_cat}, doc, upsert=True)

    def updateGameTime(self, div_id, age, gen, totalgames, totalbrackets):
        query = {gameday_id_CONST:gameday_id, venue_CONST:venue,
                 start_time_CONST:old_start_time}
        updatefields = {"$set":{start_time_CONST:new_start_time}}
        logging.debug("dbinterface:updateGameTime: query=%s, update=%s", query, updatefields)
        result_obj = self.collection.update(query, updatefields, safe=True)

    def getdiv_schedule(self, age, gender):
        '''use mongodb aggregation framework to group results by shared gametime.
        query for all rounds at once - alternate way is to loop query based
        on round id/gameday id (knowing total number of games in season)
        but that potentially does not work if a division ends up not having
        any games on a particular game day.
        ref docs.mongodb.org/manual/reference/aggregation/
        http://stackoverflow.com/questions/14770170/how-to-find-mongo-documents-with-a-same-field
        also see aggregation 'mongodb definitive guide'
        col.aggregate({$match:{AGE:'U12',GEN:'B'}}, {$group:{_id:{GAMEDAY_ID:'$GAMEDAY_ID',START_TIME:"$START_TIME"},count:{$sum:1},docs:{$push:{HOME:'$HOME',AWAY:'$AWAY',VENUE:'$VENUE'}}}},{$sort:{'_id.GAMEDAY_ID':1,'_id.START_TIME':1}})
        -----
        review case (lower/upper) strategy
        as a general rule, we are storing it in the db using uppercase keys, but
        converting them back to lower case when reading and especially
        transmitting it back to client.  Usually the conversion to lower case was
        happening at the type-specific db interface class (like scheddb.py),
        but sometimes that can be a hassle, especially with documents that are
        nested.
        Here you will notice that some of the keys used to save the read documents
        are already being changed to lowercase
        ---
        Note there are alternative syntax for $push - see http://docs.mongodb.org/manual/reference/operator/update/push/
        ---
        Update - sort order problem w pymongo - sorting w game_date and start_time -
        with game_date first and start_time second, does not work, as the result
        always to seem to sort on start_time first and game_date second, reversing
        the order between the two sort variables.
        NOTE this problem does NOT occur when using straight Mongo commands from the
        Mongo shell.
        Tried using both string representations of game_date and start_time - same
        erroneous results.
        Note that using start_time as time objects presents two problems - timedelta
        additions/subtractions are not supported with time objects, and time objects
        are not supported with mongodb, though datetime and date objects are.
        Workaround is to use a scalar value - use toordinal()/fromordinal() on
        dt/date object go get an integer mapping of the date - use this just for the
        date object.  DT rep of the time object can remain the same for the sort
        order to occur correctly.
        '''
        result_list = self.collection.aggregate([{"$match":{div_age_CONST:age,
            div_gen_CONST:gender, sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat}},
            {"$group":{'_id':{'GAME_DATE_ORD':"$GAME_DATE_ORD",
            'START_TIME':"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{'home':"$HOME", 'away':"$AWAY", 'venue':"$VENUE"}}}},
            {"$sort":{'_id.GAME_DATE_ORD':1, '_id.START_TIME':1}}])
        game_list = []
        for result in result_list:
            #print 'result',result
            sortkeys = result['_id']
            #game_date = sortkeys['GAME_DATE']
            #game_date = sortkeys[game_date_CONST].strftime(date_format_CONST)
            game_date = date.fromordinal(sortkeys['GAME_DATE_ORD']).strftime(date_format_CONST)
            start_time = sortkeys[start_time_CONST].strftime(time_format_CONST)
            #start_time = sortkeys['START_TIME']
            gameday_data = result[gameday_data_CONST]
            game_list.append({'game_date':game_date, 'start_time':start_time,
                'gameday_data':gameday_data})
        return game_list

    def getelimdiv_schedule(self,age, gender):
        # this db read involves match_id
        result_list = self.collection.aggregate([{"$match":{div_age_CONST:age,
            div_gen_CONST:gender, sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat}},
            {"$group":{'_id':{'GAME_DATE_ORD':"$GAME_DATE_ORD",
            'START_TIME':"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{'home':"$HOME", 'away':"$AWAY", 'venue':"$VENUE",
            'match_id':"$MATCH_ID", 'comment':"$COMMENT", 'around':"$AROUND"}}}},{"$sort":{'_id.GAME_DATE_ORD':1, '_id.START_TIME':1}}])
        game_list = []
        for result in result_list:
            #print 'result',result
            sortkeys = result['_id']
            game_date = date.fromordinal(sortkeys['GAME_DATE_ORD']).strftime(date_format_CONST)
            start_time = sortkeys['START_TIME'].strftime(time_format_CONST)
            gameday_data = result[gameday_data_CONST]
            game_list.append({'game_date':game_date, 'start_time':start_time,
                'gameday_data':gameday_data})
        return game_list

    def findDivisionSchedule(self, age, gender, min_game_id=None):
        # use mongodb aggregation framework to group results by shared gametime.
        # query for all rounds at once - alternate way is to loop query based
        # on round id/gameday id (knowing total number of games in season)
        # but that potentially does not work if a division ends up not having
        # any games on a particular game day.

        # ref docs.mongodb.org/manual/reference/aggregation/
        # http://stackoverflow.com/questions/14770170/how-to-find-mongo-documents-with-a-same-field
        # also see aggregation 'mongodb definitive guide'
        # col.aggregate({$match:{AGE:'U12',GEN:'B'}}, {$group:{_id:{GAMEDAY_ID:'$GAMEDAY_ID',START_TIME:"$START_TIME"},count:{$sum:1},docs:{$push:{HOME:'$HOME',AWAY:'$AWAY',VENUE:'$VENUE'}}}},{$sort:{'_id.GAMEDAY_ID':1,'_id.START_TIME':1}})
        if min_game_id:
            result_list = self.collection.aggregate([{"$match":{age_CONST:age,gen_CONST:gender, gameday_id_CONST:{"$gte":min_game_id}}},{"$group":{'_id':{gameday_id_CONST:"$GAMEDAY_ID",start_time_CONST:"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{home_CONST:"$HOME", away_CONST:"$AWAY", venue_CONST:"$VENUE"}}}},{"$sort":{'_id.GAMEDAY_ID':1, '_id.START_TIME':1}}])
        else:
            result_list = self.collection.aggregate([{"$match":{age_CONST:age,gen_CONST:gender}},
                {"$group":{'_id':{gameday_id_CONST:"$GAMEDAY_ID",
                start_time_CONST:"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{home_CONST:"$HOME", away_CONST:"$AWAY", venue_CONST:"$VENUE"}}}},
                {"$sort":{'_id.GAMEDAY_ID':1, '_id.START_TIME':1}}])
        game_list = []
        for result in result_list:
            #print 'result',result
            sortkeys = result['_id']
            gameday_id = sortkeys[gameday_id_CONST]
            start_time = sortkeys[start_time_CONST]
            gameday_data = result[gameday_data_CONST]
            game_list.append({gameday_id_CONST:gameday_id, start_time_CONST:start_time,
                              gameday_data_CONST:gameday_data})
        return game_list

    def findElimTournDivisionSchedule(self,age, gender, min_game_id=None):
        # see comments for findDivisionSchedule
        # this db read involves match_id
        if min_game_id:
            result_list = self.collection.aggregate([{"$match":{age_CONST:age,gen_CONST:gender, gameday_id_CONST:{"$gte":min_game_id}}},{"$group":{'_id':{gameday_id_CONST:"$GAMEDAY_ID",start_time_CONST:"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{home_CONST:"$HOME", away_CONST:"$AWAY", venue_CONST:"$VENUE", match_id_CONST:"$MATCH_ID", comment_CONST:"$COMMENT", round_CONST:"$ROUND"}}}},{"$sort":{'_id.GAMEDAY_ID':1, '_id.START_TIME':1}}])
        else:
            result_list = self.collection.aggregate([{"$match":{age_CONST:age,gen_CONST:gender}},
                {"$group":{'_id':{gameday_id_CONST:"$GAMEDAY_ID",start_time_CONST:"$START_TIME"},'count':{"$sum":1},gameday_data_CONST:{"$push":{home_CONST:"$HOME", away_CONST:"$AWAY", venue_CONST:"$VENUE", match_id_CONST:"$MATCH_ID", comment_CONST:"$COMMENT", round_CONST:"$ROUND"}}}},{"$sort":{'_id.GAMEDAY_ID':1, '_id.START_TIME':1}}])
        game_list = []
        for result in result_list:
            #print 'result',result
            sortkeys = result['_id']
            gameday_id = sortkeys[gameday_id_CONST]
            start_time = sortkeys[start_time_CONST]
            gameday_data = result[gameday_data_CONST]
            game_list.append({gameday_id_CONST:gameday_id, start_time_CONST:start_time,
                              gameday_data_CONST:gameday_data})
        return game_list

    def getteam_schedule(self, team_id, div_age, div_gen):
        team_game_curs = self.collection.find(
            {div_age_CONST:div_age, div_gen_CONST:div_gen,
            sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat,
            "$or":[{home_CONST:team_id},{away_CONST:team_id}]},
            {'_id':0, div_age_CONST:0, div_gen_CONST:0})
        team_game_curs.sort([('GAME_DATE_ORD',1),(start_time_CONST,1)])
        team_game_list = []
        for team_game in team_game_curs:
            team_game_list.append({
                'game_date':team_game[game_date_CONST].strftime(date_format_CONST),
                'start_time':team_game[start_time_CONST].strftime(time_format_CONST),
                'venue':team_game[venue_CONST],
                'home':team_game[home_CONST],
                'away':team_game[away_CONST]})
        return team_game_list

    def getfield_schedule(self, venue_id):
        # see comments in getdiv_schedule for logic on using game_date_ord
        # (ordinal of game date) instead of the datetime representation
        # game_date itself.  Sort order does not work when two datetime
        # variables are used for the sort
        field_game_curs = self.collection.find({venue_CONST:venue_id,
            sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {'_id':0, venue_CONST:0})
        field_game_curs.sort([('GAME_DATE_ORD',1),(start_time_CONST,1)])
        field_game_list = []
        for field_game in field_game_curs:
            field_game_list.append({
                'game_date':date.fromordinal(field_game['GAME_DATE_ORD']).strftime(date_format_CONST),
                'start_time':field_game[start_time_CONST].strftime(time_format_CONST),
                'div_age':field_game[div_age_CONST],
                'div_gen':field_game[div_gen_CONST],
                'home':field_game[home_CONST],
                'away':field_game[away_CONST]})
        return field_game_list

    def gettimeslot_metrics(self, div_age, div_gen, divfield_list, fieldinfo_tuple):
        ''' find number of earlies/latest slots for each team
        '''
        fieldinfo_list = fieldinfo_tuple.dict_list
        fieldinfo_indexerGet = fieldinfo_tuple.indexerGet
        latest_teams = []
        earliest_teams = []
        # even if fields have different totalfielddays and even completely independent
        # calendar dates, it is ok to combine the search for early latest game counters
        # into one aggreation command per 'fieldday' as the counters are still
        # 'linearly independent'
        max_totalfielddays = max(fieldinfo_list[fieldinfo_indexerGet(x)]['tfd'] for x in divfield_list)
        for fieldday_id in range(1, max_totalfielddays+1):
            result = self.collection.aggregate([
                {"$match":{venue_CONST:{"$in":divfield_list},
                fieldday_id_CONST:fieldday_id,
                sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
                SCHED_CAT:self.sched_cat}},
                {"$group":{'_id':{'start_time':"$START_TIME", 'venue':"$VENUE"},
                'data':{"$push":{'home':"$HOME", 'away':"$AWAY",
                'div_age':"$DIV_AGE", 'div_gen':"$DIV_GEN"}}}},
                {"$sort":{'_id.start_time':1}},
                {"$group":{'_id':"$_id.venue",
                'earliest':{"$first":{'data':"$data", 'time':"$_id.start_time"}},
                'latest':{"$last":{'data':"$data", 'time':"$_id.start_time"}}}},
                {"$project":{'_id':0, 'venue':"$_id", 'earliest':1,'latest':1}}])
            earliest_home = [x['earliest']['data'][0]['home']
                             for x in result
                             if x['earliest']['data'][0]['div_age']==div_age and x['earliest']['data'][0]['div_gen']==div_gen]
            earliest_away = [x['earliest']['data'][0]['away']
                             for x in result
                             if x['earliest']['data'][0]['div_age']==div_age and x['earliest']['data'][0]['div_gen']==div_gen]
            latest_home = [x['latest']['data'][0]['home']
                           for x in result
                           if x['latest']['data'][0]['div_age']==div_age and x['latest']['data'][0]['div_gen']==div_gen]
            latest_away = [x['latest']['data'][0]['away']
                           for x in result
                           if x['latest']['data'][0]['div_age']==div_age and x['latest']['data'][0]['div_gen']==div_gen]
            logging.debug("dbinterface:gettimeslot_metrics:query result=%s earliest home=%s earliest away=%s",
                          result, earliest_home, earliest_away)
            logging.debug("dbinterface:gettimeslot_metrics: latest home=%s latest away=%s",
                          latest_home, latest_away)
            earliest_teams += earliest_home + earliest_away
            latest_teams += latest_home + latest_away
        # ref http://stackoverflow.com/questions/2600191/how-to-count-the-occurrences-of-a-list-item-in-python
        latest_counter_dict = Counter(latest_teams)
        earliest_counter_dict = Counter(earliest_teams)
        logging.debug("dbinterface:gettimeslot_metrics div=%s%s earliest_teams=%s, earliest_counter_dict=%s",
            div_age, div_gen, earliest_teams, earliest_counter_dict)
        logging.debug("dbinterface:gettimeslot_metrics latest_teams=%s, latest_counter_dict=%s",
            latest_teams, latest_counter_dict)
        EL_counter = namedtuple('EL_counter','earliest latest')
        return EL_counter(earliest_counter_dict, latest_counter_dict)


    def getTimeSlotMetrics(self, age, gender, fields, totalgamedays):
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
        for gameday_id in range(1,totalgamedays+1):
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
            result = self.collection.aggregate([{"$match":{venue_CONST:{"$in":fields},
                gameday_id_CONST:gameday_id}},
                {"$group":{'_id':{'start_time':"$START_TIME",'venue':"$VENUE"},
                'data':{"$push":{'home':"$HOME", 'away':"$AWAY", 'gen':"$GEN",
                'age':"$AGE"}}}},
                {"$sort":{'_id.start_time':1}},
                {"$group":{'_id':"$_id.venue",
                'earliest':{"$first":{'data':"$data", 'time':"$_id.start_time"}},
                'latest':{"$last":{'data':"$data", 'time':"$_id.start_time"}}}},
                {"$project":{'_id':0, 'venue':"$_id", 'earliest':1,'latest':1}}])

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

    def getfairness_metrics(self, div_age, div_gen, divinfo, fieldinfo_tuple):
        '''Updated information of computing metrics for generated schedule'''
        logging.debug("dbinterface:getfairness_metrics: age %s gen %s",div_age, div_gen)
        totalteams = divinfo['totalteams']
        divfield_list = divinfo['divfield_list']
        ELcounter_tuple = self.gettimeslot_metrics(div_age, div_gen, divfield_list,
            fieldinfo_tuple)
        earliest_counter_dict = ELcounter_tuple.earliest
        latest_counter_dict = ELcounter_tuple.latest
        fieldinfo_list = fieldinfo_tuple.dict_list
        fieldinfo_indexerGet = fieldinfo_tuple.indexerGet
        metrics_list = []
        for team_id in range(1, totalteams+1):
            games_total = self.collection.find(
                {div_age_CONST:div_age, div_gen_CONST:div_gen,
                sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
                SCHED_CAT:self.sched_cat,
                "$or":[{home_CONST:team_id},{away_CONST:team_id}]
                }).count()
            homegames_total = self.collection.find(
                {div_age_CONST:div_age, div_gen_CONST:div_gen,
                sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
                SCHED_CAT:self.sched_cat,
                home_CONST:team_id}).count()
            homegames_ratio = float(homegames_total)/float(games_total)
            field_count_list = []
            for field_id in divfield_list:
                #field_name = fieldinfo_list[fieldinfo_indexerGet(field_id)]
                field_count = self.collection.find(
                    {div_age_CONST:div_age, div_gen_CONST:div_gen,
                    venue_CONST:field_id, sched_type_CONST:self.sched_type,
                    USER_ID:self.userid_name, SCHED_CAT:self.sched_cat,
                    "$or":[{home_CONST:team_id},{away_CONST:team_id}]
                    }).count()
                field_count_list.append({'field_id':field_id,
                    'field_count':field_count})
            metrics_list.append({'team_id':team_id, 'games_total':games_total,
                'homegames_ratio':homegames_ratio,
                'field_count_list':field_count_list,
                'earliest_count':earliest_counter_dict[team_id],
                'latest_count':latest_counter_dict[team_id]})
        return metrics_list

    def dropGameDocuments(self, gameday_list=None):
        # remove documents only have to do with game data
        if gameday_list:
          for gameday_id in gameday_list:
            self.collection.remove({gameday_id_CONST:gameday_id})
        else:
          self.collection.remove({gameday_id_CONST:{"$exists":True}})
        # reset status
        self.setSchedStatus_col(0)

    def dropgame_docs(self):
        '''new version - remove documents only have to do with game schedule
        data '''
        self.collection.remove({game_date_CONST:{"$exists":True},
            sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat})
        # reset status
        self.setSchedStatus_col(0)

    def setSchedStatus_col(self, value):
        self.collection.update({sched_status_CONST:{"$exists":True},
            sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {"$set":{sched_status_CONST:value}})

    def getSchedStatus(self):
        return self.collection.find_one({sched_status_CONST:{"$exists":True},
            sched_type_CONST:self.sched_type, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat})[sched_status_CONST]

    def getScheduleCollection(self, db_col_type, userid_name, sched_cat):
        # ref http://api.mongodb.org/python/current/api/pymongo/database.html
        # make sure python version >= 2.7 for include_system_collections
        # note that only instance of the dbname is present in the returned list if
        # db_col_type_list includes multiple entries and the same db name exists
        # corresponding to the multiple db_col_types (see use of 'any' below)
        rawsc_list = self.schedule_db.collection_names(include_system_collections=False)
        # first find list of collections that satisfy the existence of config_status,
        # and matches user_id and sched_type
        sc_list = [x for x in rawsc_list if self.schedule_db[x].find_one({
            sched_type_CONST:str(db_col_type), CONFIG_STATUS:{"$exists":True},
            'USER_ID':userid_name, SCHED_CAT:sched_cat})]
        # technically possible to do in one messy list comprehension, but break out
        # extracting config_status into the below list comprehension.
        # add distr_db_type to each db_collection dictionary
        sc_config_list = list()
        for x in sc_list:
            col = self.schedule_db[x].find_one({
                sched_type_CONST:str(db_col_type),
                CONFIG_STATUS:{"$exists":True},
                USER_ID:userid_name, SCHED_CAT:sched_cat})
            if DIVSTR_DB_TYPE in col:
                sc_dict = {'name':x, 'config_status':col[CONFIG_STATUS],
                    'divstr_db_type':col[DIVSTR_DB_TYPE]}
            else:
                sc_dict = {'name':x, 'config_status':col[CONFIG_STATUS]}
            sc_config_list.append(sc_dict)
        return sc_config_list

    def getUserCollection(self):
        # ref http://api.mongodb.org/python/current/api/pymongo/database.html
        # make sure python version >= 2.7 for include_system_collections
        # note that only instance of the dbname is present in the returned list if
        # db_col_type_list includes multiple entries and the same db name exists
        # corresponding to the multiple db_col_types (see use of 'any' below)
        rawsc_list = self.schedule_db.collection_names(include_system_collections=False)
        # check for size of collection because if size is one, it only includes the SCHED_STATUS doc
        sc_list = [x for x in rawsc_list if self.schedule_db[x].find_one({
            sched_type_CONST:str(DB_Col_Type.UserInfo)})]
        return sc_list

    def getCupScheduleCollections(self):
        sc_list = self.schedule_db.collection_names(include_system_collections=False)
        # check for size of collection because if size is one, it only includes the SCHED_STATUS doc
        schedcollect_list = [x for x in sc_list
                             if self.schedule_db[x].count() > 1 and self.schedule_db[x].find_one({sched_type_CONST:str(DB_Col_Type.ElimTourn)}) ]
        return schedcollect_list

    def getInfoDocument(self, id_str):
        result = self.collection.find_one({sched_type_CONST:self.sched_type,
            sched_status_CONST:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {'_id':0})
        config_status = result[CONFIG_STATUS]
        info_curs = self.collection.find({sched_type_CONST:self.sched_type,
            id_str:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat}, {'_id':0})
        # convert cursor to list
        info_list = list(info_curs)
        return _List_Result(info_list, result)

    def getInfoPlusDocument(self, id_str):
        # similar to getInfoDocument, but also get divstr info in db and return
        # as separate parameters
        result = self.collection.find_one({sched_type_CONST:self.sched_type,
            sched_status_CONST:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat},
            {'_id':0})
        config_status = result[CONFIG_STATUS]
        divstr_colname = result[divstr_colname_CONST]
        divstr_db_type = result[DIVSTR_DB_TYPE]
        info_curs = self.collection.find({sched_type_CONST:self.sched_type,
            id_str:{"$exists":True}, USER_ID:self.userid_name,
            SCHED_CAT:self.sched_cat}, {'_id':0})
        # convert cursor to list
        info_list = list(info_curs)
        return _PlusList_Status(info_list, config_status, divstr_colname,
                            divstr_db_type)

    def getDocuments(self, query_obj):
        query_obj.update({sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat})
        doc_curs = self.collection.find(query_obj, {'_id':0})
        doc_list = list(doc_curs)
        return doc_list

    def getSchedType_doc(self, query_obj):
        # get schedule type - don't have to return sched_type, user, or config_status
        query_obj.update({sched_type_CONST:self.sched_type,
            USER_ID:self.userid_name, SCHED_CAT:self.sched_cat})
        result = self.collection.find(query_obj,
            {'_id':0, sched_type_CONST:0, USER_ID:0, CONFIG_STATUS:0,
            SCHED_CAT:0}).limit(1)
        return list(result)[0]

    def getFieldInfo(self):
        result_list = self.collection.find({field_id_CONST:{"$exists":True}},{'_id':0}).sort(field_id_CONST, 1)
        fieldinfo_list = []
        for field_dict in result_list:
            fieldinfo_list.append(field_dict)
        f_indexerGet = lambda x: dict((p[field_id_CONST],i) for i,p in enumerate(fieldinfo_list)).get(x)
        return _List_Indexer(fieldinfo_list, f_indexerGet)

    def drop_collection(self):
        query_obj = {"SCHED_TYPE":self.sched_type, USER_ID:self.userid_name,
        SCHED_CAT:self.sched_cat}
        self.collection.delete_many(query_obj)
        # if no documents are left, then actually drop collection
        if not self.collection.find().limit(1).count():
            self.collection.drop()
