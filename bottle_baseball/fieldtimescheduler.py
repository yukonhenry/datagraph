from datetime import  datetime, timedelta
from itertools import cycle
from schedule_util import roundrobin, all_same, all_value
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision, getFieldSeasonStatus_list
import logging
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
# http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
time_format_CONST = '%H:%M'
#http://www.tutorialspoint.com/python/python_classes_objects.htm
class FieldTimeScheduleGenerator:
    def __init__(self, leaguedivinfo, fieldinfo, connected_comp, dbinterface):
        self.leaguedivinfo = leaguedivinfo
        self.connected_div_components = connected_comp
        self.fieldSeasonStatus = getFieldSeasonStatus_list()
        self.fieldinfo = fieldinfo
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.leaguedivinfo)+1):
            self.total_game_dict[i] = []
        self.dbinterface = dbinterface

    def findMinimumCountField(self, homemetrics_list, awaymetrics_list):
        homemetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(homemetrics_list))
        awaymetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(awaymetrics_list))
        home_field_list = [x['field_id'] for x in homemetrics_list]
        away_field_list = [x['field_id'] for x in awaymetrics_list]
        if (set(home_field_list) != set(away_field_list)):
            logging.error("home and away teams have different field lists %s %s",home_field_list, away_field_list)
            return False
        else:
            # we need to first sort the lists
            sumcount_list = [x+y for (x,y) in zip([i['count'] for i in homemetrics_list],
                                                  [j['count'] for j in awaymetrics_list])]
            # refer to http://stackoverflow.com/questions/3989016/how-to-find-positions-of-the-list-maximum

    def generateSchedule(self, total_match_list):
        # ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
        # for finding index of dictionary key in array of dictionaries
        # use indexer so that we don't depend on order of divisions in total_match_list
        # alternate method http://stackoverflow.com/questions/3179106/python-select-subset-from-list-based-on-index-set
        # indexer below is used to protect against list of dictionaries that are not ordered according to id,
        # though it is a protective measure, as the list should be ordered with the id.
        match_list_indexer = dict((p['div_id'],i) for i,p in enumerate(total_match_list))
        leaguediv_indexer = dict((p['div_id'],i) for i,p in enumerate(self.leaguedivinfo))
        fieldinfo_indexer = dict((p['field_id'],i) for i,p in enumerate(self.fieldinfo))

        self.dbinterface.dropGameCollection()  # reset game schedule collection

        # work with each set of connected divisions w. shared field
        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            submatch_list = []
            gameinterval_dict = {}
            targetfieldcount_list = []
            fieldmetrics_list = []
            max_submatchrounds = 0
            # take one of those connected divisions and iterate through each division
            for div_id in connected_div_list:
                divindex = leaguediv_indexer.get(div_id)
                divinfo = self.leaguedivinfo[divindex]
                divfields = divinfo['fields']
                numteams = divinfo['totalteams']
                fset.update(divfields)  #incremental union to set of shareable fields
                # http://docs.python.org/2/library/datetime.html#timedelta-objects
                # see also python-in-nutshell
                # convert gameinterval into datetime.timedelta object
                ginterval = divinfo['gameinterval']
                gameinterval_dict[div_id] = timedelta(0,0,0,0,ginterval)
                index = match_list_indexer.get(div_id)
                # get match list for indexed division
                divmatch_dict = total_match_list[index]
                submatch_list.append(divmatch_dict)
                # calculate number of rounds (gameslots) for the division, and update max if it is the largest
                # amongst connected divisions
                submatchrounds = len(divmatch_dict['match_list'])
                if submatchrounds > max_submatchrounds:
                    max_submatchrounds = submatchrounds
                # describe target fair field usage cout
                numdivfields = len(divfields)
                # get number of games scheduled for each team in dvision
                numgames_list = divmatch_dict['numgames_list']
                logging.debug("divsion=%d numgames_list=%s",division,numgames_list)
                # for each team, number of games targeted for each field.
                # similar to homeaway balancing number can be scalar (if #teams/#fields is mod 0)
                # or it can be a two element range (floor(#teams/#fields), same floor+1)
                # the target number of games per fields is the same for each field
                numgamesperfield_list = [[n/numdivfields] if n%numdivfields==0 else [n/numdivfields,n/numdivfields+1] for n in numgames_list]
                targetfieldcount_list.append({'div_id':division, 'targetperfield':numgamesperfield_list})

                fmetrics_list = numteams*[[{'field_id':x, 'count':0} for x in divfields]]
                fieldmetrics_list.append({'div_id':division, 'fmetrics':fmetrics_list})
            logging.debug('target num games per fields=%s',targetfieldcount_list)
            # we are assuming still below that all fields in fset are shared by the field-sharing
            # divisions, i.e. we are not sufficiently handing cases where div1 uses fields [1,2]
            # and div2 is using fields[2,3] (field 2 is shared but not 1 and 3)
            flist = list(fset)
            flist.sort()  # default ordering, use it for now
            field_list = []
            initialstarttime_dict = {}
            for f_id in flist:
                # field_id is 0-index based
                findex = fieldinfo_indexer.get(f_id)
                # note convert start time string to datetime obj
                nexttime_dtime = parser.parse(self.fieldinfo[findex]['start_time'])
                field_list.append({'field_id':f_id,
                                   'next_time':nexttime_dtime})
                initialstarttime_dict[f_id] = nexttime_dtime  #use for resetting time to beginning of day
                fieldmetrics_max = 0

            fieldstatus_indexer = dict((p['field_id'],i) for i,p in enumerate(self.fieldSeasonStatus))
            fieldmetrics_indexer = dict((p['div_id'],i) for i,p in enumerate(fieldmetrics_list))
            targetfieldcount_indexer = dict((p['div_id'],i) for i,p in enumerate(targetfieldcount_list))

            for round_id in range(1,max_submatchrounds+1):
                # create combined list of matches so that it can be passed to the multiplexing
                # function 'roundrobin' below
                combined_match_list = []
                for div_dict in submatch_list:
                    divmatch_list = div_dict['match_list']
                    matchlist_indexer = dict((p[round_id_CONST],i) for i,p in enumerate(divmatch_list))
                    rindex = matchlist_indexer.get[round_id]
                    if rindex:
                        div_id = div_dict['div_id']
                        match_list = divmatch_list[rindex]
                        game_list = match_list[game_team_CONST]
                        round_match_list = []
                        for game in game_list:
                            round_match_list.append({'div_id':div_id, 'game':game, 'round_id':round_id,
                                                     'gameinterval':gameinterval_dict[div_id]})
                        combined_match_list.append(round_match_list)
                    else:
                        continue  # skip over this division if it has run out of gameslots

                # mutliplex the divisions that are sharing fields; user itertools round robin utility
                #http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
                # http://stackoverflow.com/questions/7529376/pythonic-way-to-mix-two-lists
                rrgenobj = roundrobin(combined_match_list)
                field_list_iter = cycle(field_list)
                field = field_list_iter.next()
                fieldroundstatus_list = fieldstatus_list[round_id-1]
                for rrgame in rrgenobj:
                    div_id = rrgame['div_id']
                    dindex = fieldmetrics_indexer.get(div_id)
                    teamfieldmetrics_list = fieldmetrics_list[dindex]['fmetrics']

                    field_id = field['field_id']
                    fsindex = fieldstatus_indexer.get(field_id)
                    fieldslotstatus_list = self.fieldSeasonStatus[fsindex]['slotstatus_list']

                    gameinfo = rrgame['game']
                    home_id = gameinfo[home_CONST]
                    away_id = gameinfo[away_CONST]

                    home_fieldmetrics_list = teamfieldmetrics_list[home_id-1]
                    away_fieldmetrics_list = teamfieldmetrics_list[away_id-1]

                    home_fieldcount = home_fieldmetrics_list[home_fieldmetrics_indexer.get(field_id)]['count']
                    away_fieldcount = away_fieldmetrics_list[away_fieldmetrics_indexer.get(field_id)]['count']


                    if all_value([x['count'] for x in fieldmetrics_list], fieldmetrics_max):
                        fieldmetrics_max += 1
                        metindex = fieldmetrics_indexer.get(field_id)
                    else:
                        while True:
                            metindex = fieldmetrics_indexer.get(field_id)
                            fcount = fieldmetrics_list[metindex]['count']
                            if fcount < fieldmetrics_max:
                                break
                            else:
                                field = field_list_iter.next()
                                field_id = field['field_id']
                    fieldmetrics_list[metindex]['count'] += 1
                    #print 'rr',rrgame, field, field['next_time'].strftime(time_format_CONST)
                    div = getAgeGenderDivision(div_id)
                    logging.debug('field assigned=%d for %s%s new fieldmetrics=%s', field_id, div.age, div.gender, fieldmetrics_list)
                    self.dbinterface.insertGameData(div.age, div.gender, rrgame['round_id'],
                                                    field['next_time'].strftime(time_format_CONST),
                                                    field_id,
                                                    rrgame['game'][home_CONST],
                                                    rrgame['game'][away_CONST])
                    # update next available time for the field
                    field['next_time'] += rrgame['gameinterval']
                    field = field_list_iter.next()
                # reset next available time for new round
                for f in field_list:
                    f['next_time'] = initialstarttime_dict[field['field_id']]
