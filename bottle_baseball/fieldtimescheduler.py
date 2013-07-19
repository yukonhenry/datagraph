from datetime import  datetime, timedelta
from itertools import cycle
from schedule_util import roundrobin, all_same, all_value
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision, getFieldSeasonStatus_list
import logging
from operator import itemgetter
from copy import deepcopy
from sched_exceptions import FieldAvailabilityError
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
        #logging.debug("fieldseasonstatus init=%s",self.fieldSeasonStatus)
        self.fieldinfo = fieldinfo
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.leaguedivinfo)+1):
            self.total_game_dict[i] = []
        self.dbinterface = dbinterface

    def findMinimumCountField(self, homemetrics_list, awaymetrics_list, submin=0):
        # return field_id(s) (can be more than one) that corresponds to the minimum
        # count in the two metrics list.  the minimum should map to the same fied in both
        # metric lists, but to take into account cases where field_id with min count is different
        # between two lists, use sum of counts as metric.
        # return field_id(s) - not indices
        #optional parameter submin is used when the submin-th minimum is required, i.e. is submin=1
        #return the 2nd-most minimum count fields

        # first ensure both lists are sorted according to field
        sorted_homemetrics_list = sorted(homemetrics_list, key=itemgetter('field_id'))
        sorted_awaymetrics_list = sorted(awaymetrics_list, key=itemgetter('field_id'))
        home_field_list = [x['field_id'] for x in sorted_homemetrics_list]
        away_field_list = [x['field_id'] for x in sorted_awaymetrics_list]
        if (set(home_field_list) != set(away_field_list)):
            logging.error("home and away teams have different field lists %s %s",home_field_list, away_field_list)
            return None
        # get min
        sumcount_list = [x+y for (x,y) in zip([i['count'] for i in sorted_homemetrics_list],
                                              [j['count'] for j in sorted_awaymetrics_list])]
        if (submin == 0):
            minsum = min(sumcount_list)
        else:
            try:
                minsum = sorted(sumcount_list)[submin]
            except IndexError:
                logging.error("findMinimumCountField: submin parameter too large %d, needs to be less than %d",
                              submin, len(sumcount_list))
                return None
        # refer to http://stackoverflow.com/questions/3989016/how-to-find-positions-of-the-list-maximum
        minind = [i for i, j in enumerate(sumcount_list) if j == minsum]
        mincount_fields = [home_field_list[i] for i in minind]
        return mincount_fields

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
            target_earlylate_list = []
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
                # get match list for indexed division
                divmatch_dict = total_match_list[match_list_indexer.get(div_id)]
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
                logging.debug("divsion=%d numgames_list=%s",div_id,numgames_list)
                # for each team, number of games targeted for each field.
                # similar to homeaway balancing number can be scalar (if #teams/#fields is mod 0)
                # or it can be a two element range (floor(#teams/#fields), same floor+1)
                # the target number of games per fields is the same for each field
                numgamesperfield_list = [[n/numdivfields] if n%numdivfields==0 else [n/numdivfields,n/numdivfields+1] for n in numgames_list]
                targetfieldcount_list.append({'div_id':div_id, 'targetperfield':numgamesperfield_list})

                fmetrics_list = [{'field_id':x, 'count':0} for x in divfields]
                # note below numteams*[fmetrics_list] only does a shallow copy; use deepcopy
                tfmetrics_list = [deepcopy(fmetrics_list) for i in range(numteams)]
                fieldmetrics_list.append({'div_id':div_id, 'tfmetrics':tfmetrics_list})

                earlylate_list = [{'early':numdivfields*x/numteams, 'late':numdivfields*x/numteams} for x in numgames_list]
                target_earlylate_list.append({'div_id':div_id, 'earlylate_list':earlylate_list})
            logging.debug('target num games per fields=%s',targetfieldcount_list)
            # we are assuming still below that all fields in fset are shared by the field-sharing
            # divisions, i.e. we are not sufficiently handing cases where div1 uses fields [1,2]
            # and div2 is using fields[2,3] (field 2 is shared but not 1 and 3)

            fieldstatus_indexer = dict((p['field_id'],i) for i,p in enumerate(self.fieldSeasonStatus))
            fieldmetrics_indexer = dict((p['div_id'],i) for i,p in enumerate(fieldmetrics_list))
            targetfieldcount_indexer = dict((p['div_id'],i) for i,p in enumerate(targetfieldcount_list))

            # use generatore list comprehenshion to calcuate sum of required and available fieldslots
            required_gameslotsperday = sum(total_match_list[match_list_indexer.get(d)]['gameslotsperday'] for d in connected_div_list)
            available_gameslotsperday = sum(self.fieldSeasonStatus[fieldstatus_indexer.get(f)]['gameslotsperday'] for f in fset)
            logging.debug("for divs=%s fset=%s required slots=%d available=%d",
                          connected_div_list, fset, required_gameslotsperday, available_gameslotsperday)
            if available_gameslotsperday < required_gameslotsperday:
                logging.error("!!!!!!!!!!!!!!!!")
                logging.error("Not enough game slots, need %d slots, but only %d available",
                              required_gameslotsperday, available_gameslotsperday)
                logging.error("!!!!Either add more time slots or fields!!!")

            for round_id in range(1,max_submatchrounds+1):
                # create combined list of matches so that it can be passed to the multiplexing
                # function 'roundrobin' below
                combined_match_list = []
                for div_dict in submatch_list:
                    divmatch_list = div_dict['match_list']
                    matchlist_indexer = dict((p[round_id_CONST],i) for i,p in enumerate(divmatch_list))
                    rindex = matchlist_indexer.get(round_id)
                    if rindex is not None:
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
                for rrgame in rrgenobj:
                    div_id = rrgame['div_id']
                    dindex = fieldmetrics_indexer.get(div_id)
                    teamfieldmetrics_list = fieldmetrics_list[dindex]['tfmetrics']

                    gameinfo = rrgame['game']
                    home_id = gameinfo[home_CONST]
                    away_id = gameinfo[away_CONST]

                    home_fieldmetrics_list = teamfieldmetrics_list[home_id-1]
                    away_fieldmetrics_list = teamfieldmetrics_list[away_id-1]

                    submin = 0
                    while True:
                        fieldcand_list = self.findMinimumCountField(home_fieldmetrics_list, away_fieldmetrics_list, submin)
                        if fieldcand_list is None:
                            raise FieldAvailabilityError(div_id)
                        logging.debug("----------------------")
                        logging.debug("divid=%d round_id=%d home=%d away=%d homemetrics=%s awaymetrics=%s minimum count fields=%s",
                                      div_id, round_id, home_id, away_id, home_fieldmetrics_list, away_fieldmetrics_list, fieldcand_list)
                        if len(fieldcand_list) > 1:
                            isgame_list = [(x,[y['isgame'] for y in self.fieldSeasonStatus[fieldstatus_indexer.get(x)]['slotstatus_list'][round_id-1]]) for x in fieldcand_list]
                            earliestslot_list = [(x[0],x[1].index(False)) for x in isgame_list if not all_value(x[1],True)]
                            # first get the list of field/status dictionaries before searching for the False field
                            if all_value(earliestslot_list, None):
                                logging.info("fieldtimescheduler: fields %s are full",[x[0] for x in isgame_list])
                                submin += 1
                                continue
                            # http://docs.python.org/2/howto/sorting.html
                            # sort based on first index of isgame 'False' which maps to earliest time
                            # game that needs to be filled.
                            sorted_earliestslot_list = sorted(earliestslot_list, key=itemgetter(1))
                            field_id = sorted_earliestslot_list[0][0]
                            slot_index = sorted_earliestslot_list[0][1]
                            break
                        else:
                            field_id = fieldcand_list[0]
                            fsindex = fieldstatus_indexer.get(field_id)
                            # find status list for this round
                            fieldslotstatus_list = self.fieldSeasonStatus[fsindex]['slotstatus_list'][round_id-1]
                            # find first open time slot in round
                            isgame_list = [y['isgame'] for y in fieldslotstatus_list]
                            if not all_value(isgame_list, True):
                                slot_index = isgame_list.index(False)
                                break
                            else:
                                submin += 1
                                logging.info("fieldtimescheduler: current minimum count field is all field, try another %d",
                                             submin)
                                continue

                    selected_ftstatus = self.fieldSeasonStatus[fieldstatus_indexer.get(field_id)]['slotstatus_list'][round_id-1][slot_index]
                    selected_ftstatus['isgame'] = True
                    gametime = selected_ftstatus['start_time']
                    home_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(home_fieldmetrics_list))
                    away_fieldmetrics_indexer = dict((p['field_id'],i) for i,p in enumerate(away_fieldmetrics_list))
                    home_fieldmetrics_list[home_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    away_fieldmetrics_list[away_fieldmetrics_indexer.get(field_id)]['count'] += 1
                    div = getAgeGenderDivision(div_id)
                    logging.debug("div=%s%s round_id=%d, field=%d gametime=%s slotindex=%d",
                                  div.age, div.gender, round_id, field_id, gametime, slot_index)
                    self.dbinterface.insertGameData(div.age, div.gender, rrgame['round_id'],
                                                    gametime.strftime(time_format_CONST),
                                                    field_id, home_id, away_id)
