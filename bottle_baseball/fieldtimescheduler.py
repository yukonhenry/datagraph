from datetime import  datetime, timedelta
from itertools import cycle
from schedule_util import roundrobin, all_same
#ref Python Nutshell p.314 parsing strings to return datetime obj
from dateutil import parser
from leaguedivprep import getAgeGenderDivision
from dbinterface import DBInterface

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
    def __init__(self, leaguedivinfo, fieldinfo, connected_comp):
        self.leaguedivinfo = leaguedivinfo
        self.connected_div_components = connected_comp
        self.scheduleMatrix = []
        self.fieldinfo = fieldinfo
        self.total_game_dict = {}
        # initialize dictionary (div_id is key)
        for i in range(1,len(self.leaguedivinfo)+1):
            self.total_game_dict[i] = []

        # assume greeday algorithm for now
        for field in fieldinfo:
            self.scheduleMatrix.append({'field_id':field['field_id'],
                                        'next_available':field['start_time']})
        self.dbinterface = DBInterface()

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

        # work with each set of connected divisions w. shared field
        for connected_div_list in self.connected_div_components:
            fset = set() # set of shared fields
            submatch_list = []
            submatch_len_list = []
            gameinterval_dict = {}
            # take one of those connected divisions and iterate through each division
            for division in connected_div_list:
                divindex = leaguediv_indexer.get(division)
                fset.update(self.leaguedivinfo[divindex]['fields'])  #incremental union
                # http://docs.python.org/2/library/datetime.html#timedelta-objects
                # see also python-in-nutshell
                # convert gameinterval into datetime.timedelta object
                ginterval = self.leaguedivinfo[divindex]['gameinterval']
                gameinterval_dict[division] = timedelta(0,0,0,0,ginterval)
                index = match_list_indexer.get(division)
                # get match list for indexed division
                div_match_list = total_match_list[index]
                submatch_list.append(div_match_list)
                submatch_len_list.append(len(div_match_list['match_list']))  #gives num rounds
            if not all_same(submatch_len_list):
                print 'different number of games per season amongst shared field NOT SUPPORTED'
                return None

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
            print 'fieldlist', field_list
            # max below is not sufficient if there are differences in season per games
            # within the divisions that share fields
            for round_index in xrange(max(submatch_len_list)):
                combined_match_list = []
                for division_dict in submatch_list:
                    div_id = division_dict['div_id']
                    match_list = division_dict['match_list'][round_index]
                    round_id = match_list[round_id_CONST]
                    print 'round id', round_id
                    game_list = match_list[game_team_CONST]
                    round_match_list = []
                    for game in game_list:
                        round_match_list.append({'div_id':div_id, 'game':game, 'round_id':round_id,
                                                 'gameinterval':gameinterval_dict[div_id]})
                    combined_match_list.append(round_match_list)
                # mutliplex the divisions that are sharing fields; user itertools round robin utility
                #http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
                # http://stackoverflow.com/questions/7529376/pythonic-way-to-mix-two-lists
                rrgenobj = roundrobin(combined_match_list)
                field_list_iter = cycle(field_list)
                field = field_list_iter.next()
                for rrgame in rrgenobj:
                    print 'rr',rrgame, field, field['next_time'].strftime(time_format_CONST)
                    div = getAgeGenderDivision(rrgame['div_id'])
                    game_dict = {age_CONST:div.age,
                                 gen_CONST:div.gender,
                                 round_id_CONST:rrgame['round_id'],
                                 start_time_CONST:field['next_time'].strftime(time_format_CONST),
                                 venue_CONST:field['field_id'],
                                 home_CONST:rrgame['game'][home_CONST],
                                 away_CONST:rrgame['game'][away_CONST]}
                    print 'game_dict', game_dict

                    # update next available time for the field
                    field['next_time'] += rrgame['gameinterval']
                    field = field_list_iter.next()
                # reset next available time for new round
                for f in field_list:
                    f['next_time'] = initialstarttime_dict[field['field_id']]
