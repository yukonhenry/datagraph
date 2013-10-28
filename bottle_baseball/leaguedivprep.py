#!/usr/local/bin/python2.7
''' Copyright YukonTR 2013 '''
import simplejson as json
import time
import networkx as nx
from networkx import connected_components
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph
# ref http://stackoverflow.com/questions/2970608/what-are-named-tuples-in-python for namedtuples
from collections import namedtuple
from datetime import timedelta
from dateutil import parser
from copy import deepcopy
from operator import itemgetter
import logging

_List_Indexer = namedtuple('_List_Indexer', 'dict_list indexerGet')

_league_div = [
{ 'div_id':1, 'agediv':'U06', 'gender':'B', 'totalteams':15,
  'gameinterval':60, 'gamesperseason':10},
{ 'div_id':2, 'agediv':'U06', 'gender':'G', 'totalteams':8,
  'gameinterval':60, 'gamesperseason':10},
{ 'div_id':3, 'agediv':'U08', 'gender':'B', 'totalteams':41,
  'gameinterval':70, 'gamesperseason':10},
{ 'div_id':4, 'agediv':'U08', 'gender':'G', 'totalteams':28,
  'gameinterval':70, 'gamesperseason':10},
{ 'div_id':5, 'agediv':'U10', 'gender':'B', 'totalteams':23,
  'gameinterval':80, 'gamesperseason':10},
{ 'div_id':6, 'agediv':'U10', 'gender':'G', 'totalteams':22,
  'gameinterval':80, 'gamesperseason':10},
{ 'div_id':7, 'agediv':'U12', 'gender':'B', 'totalteams':15,
  'gameinterval':90, 'gamesperseason':10},
{ 'div_id':8, 'agediv':'U12', 'gender':'G', 'totalteams':13,
  'gameinterval':90, 'gamesperseason':10}
]
#assign team numbers
team_id_start = 1
for div in _league_div:
	next_team_id_start = team_id_start + div['totalteams']
	div['team_id_range'] = (team_id_start, next_team_id_start-1)
        team_id_start = next_team_id_start

# primary key identifies age groups that have priority for the fields.
# identified by _id from _league_div dictionary elements
_field_info = [
        {'field_id':1, 'primary':[1,2], 'secondary':[3,4], 'name':'Sequoia Elem 1',
         'start_time':'09:00', 'end_time':'18:00'},
        {'field_id':2, 'primary':[1,2], 'secondary':[3,4], 'name':'Sequoia Elem 2',
         'start_time':'09:00', 'end_time':'18:00'},
        {'field_id':3, 'primary':[3,4], 'secondary':[1,2], 'name':'Pleasant Hill Elem 1',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':4, 'primary':[3,4], 'secondary':[1,2], 'name':'Pleasant Hill Elem 2',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':5, 'primary':[3,4], 'secondary':[1,2], 'name':'Pleasant Hill Elem 3',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':6, 'primary':[3,4], 'secondary':[1,2], 'name':'Golden Hills 1',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':7, 'primary':[3,4], 'secondary':[1,2], 'name':'Golden Hills 2',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':8, 'primary':[3,4], 'secondary':[1,2], 'name':'Mountain View Park',
         'start_time':'09:00', 'end_time':'18:00'},
        {'field_id':9, 'primary':[5,6], 'secondary':[1,2], 'name':'Pleasant Hill Middle 1',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':10, 'primary':[5,6], 'secondary':[1,2], 'name':'Pleasant Hill Middle 2',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':11, 'primary':[5,6], 'secondary':[1,2], 'name':'Pleasant Hill Middle 3',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':12, 'primary':[5,6], 'secondary':[1,2], 'name':'Nancy Boyd Park',
         'start_time':'09:00', 'end_time':'18:00' },
        {'field_id':13, 'primary':[5,6], 'secondary':[1,2], 'name':'Strandwood Elem',
         'start_time':'09:00', 'end_time':'18:00' },
#    {'field_id':14, 'primary':[5,6], 'secondary':[1,2], 'name':'Morello Park',
#     'start_time':'13:30', 'end_time':'16:30', 'closed_gameday_list':[4] },
        {'field_id':14, 'primary':[7,8], 'secondary':[1,2], 'name':'Sequoia Middle',
         'start_time':'09:00', 'end_time':'18:00'},
        {'field_id':15, 'primary':[7,8], 'secondary':None, 'name':'Gregory Gardens Elem',
         'start_time':'09:00', 'end_time':'18:00'},
        {'field_id':16, 'primary':[7,8], 'secondary':None, 'name':'Pleasant Hill Park',
         'start_time':'09:00', 'end_time':'18:00'}
#    {'field_id':18, 'primary':[9,10], 'secondary':None, 'name':'Las Juntas Elem',
#     'start_time':'09:00', 'end_time':'18:00',
#     'unavailable':[{'start':'10/28/13','end':'10/28/13'}]}
]

# assigned fields attribute for each division
# ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
# for finding index of dictionary key in array of dictionaries
# use indexer so that we don't depend on order of divisions in league_div list
_div_indexer = dict((p['div_id'],i) for i,p in enumerate(_league_div))
for field in _field_info:
	f_id = field['field_id']
	for d_id in field['primary']:
		index = _div_indexer.get(d_id)
		if index is not None:
			division = _league_div[index]
			# check existence of key 'fields' - if it exists, append to list of fields, if not create
			if 'fields' in division:
				division['fields'].append(f_id)
			else:
				division['fields'] = [f_id]

# for tournament fields - node U10 is div_id 1 and so on
_tournament_field_info = [
    {'field_id':9, 'primary':[1,2], 'secondary':[1,2], 'name':'Pleasant Hill Middle 1',
    'start_time':'08:30', 'end_time':'16:30', 'numgamedays':6,'limiteddays':[{'gameday':6, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':1, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':2, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':10, 'primary':[1,2], 'secondary':[1,2], 'name':'Pleasant Hill Middle 2',
    'start_time':'08:30', 'end_time':'16:30', 'numgamedays':6,
    'limiteddays':[{'gameday':6, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':1, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':2, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':11, 'primary':[1,2], 'secondary':[1,2], 'name':'Pleasant Hill Middle 3',
    'start_time':'08:30', 'end_time':'16:30', 'numgamedays':6,
    'limiteddays':[{'gameday':6, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':1, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':2, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':12, 'primary':[1,2], 'secondary':[1,2], 'name':'Nancy Boyd Park',
    'start_time':'08:30', 'end_time':'16:30', 'numgamedays':6,
    'limiteddays':[{'gameday':6, 'start_time':'13:00', 'end_time':'17:00'},{'gameday':1, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':2, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':13, 'primary':[1,2], 'secondary':[1,2], 'name':'Strandwood Elem',
    'start_time':'08:30', 'end_time':'16:30', 'numgamedays':6,
    'limiteddays':[{'gameday':6, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':1, 'start_time':'09:00', 'end_time':'17:00'},{'gameday':2, 'start_time':'09:00', 'end_time':'17:00'}]},
#   {'field_id':14, 'primary':[5,6], 'secondary':[1,2], 'name':'Morello Park',
#   'start_time':'13:30', 'end_time':'16:30', 'closed_gameday_list':[4] },
    {'field_id':14, 'primary':[3,4], 'secondary':[1,2], 'name':'Sequoia Middle',
    'start_time':'08:00', 'end_time':'17:00', 'numgamedays':6,
    'limiteddays':[{'gameday':4, 'start_time':'08:00', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'09:00', 'end_time':'17:00'},
    {'gameday':6, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':15, 'primary':[3,4], 'secondary':None, 'name':'Gregory Gardens Elem',
    'start_time':'08:00', 'end_time':'17:00', 'numgamedays':6,
    'limiteddays':[{'gameday':4, 'start_time':'08:00', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'09:00', 'end_time':'17:00'},
    {'gameday':6, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':16, 'primary':[3,4], 'secondary':None, 'name':'Pleasant Hill Park',
    'start_time':'09:00', 'end_time':'17:00', 'numgamedays':6, 'closed_gameday_list':[4,6],
    'limiteddays':[{'gameday':4, 'start_time':'09:00', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'09:00', 'end_time':'17:00'},
    {'gameday':6, 'start_time':'09:00', 'end_time':'17:00'}]},
    {'field_id':17, 'primary':[5,6], 'secondary':None, 'name':'Sequoia Middle Large',
    'start_time':'09:00', 'end_time':'17:00', 'numgamedays':6,
    'limiteddays':[{'gameday':2, 'start_time':'09:30', 'end_time':'17:00'},
    {'gameday':1, 'start_time':'08:30', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'08:30', 'end_time':'17:00'}]},
    {'field_id':18, 'primary':[5,6], 'secondary':None, 'name':'Hidden Lakes',
    'start_time':'09:00', 'end_time':'17:00', 'numgamedays':6,
    'limiteddays':[{'gameday':1, 'start_time':'08:30', 'end_time':'17:00'},{'gameday':2, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':4, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'08:30', 'end_time':'17:00'},
    {'gameday':6, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':1, 'start_time':'08:30', 'end_time':'17:00'}]},
    {'field_id':19, 'primary':[5,6], 'secondary':None, 'name':'Waterfront',
    'start_time':'09:00', 'end_time':'17:00', 'numgamedays':6,
    'limiteddays':[{'gameday':1, 'start_time':'08:30', 'end_time':'17:00'},
    {'gameday':2, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':4, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':5, 'start_time':'08:30', 'end_time':'17:00'},
    {'gameday':6, 'start_time':'13:30', 'end_time':'17:00'},
    {'gameday':1, 'start_time':'08:30', 'end_time':'17:00'}]},
    {'field_id':20, 'primary':[5,6], 'secondary':None, 'name':'College Park Turf',
    'start_time':'14:00', 'end_time':'17:00', 'numgamedays':6,
    'closed_gameday_list':[1,3,5]}
    #'limiteddays':[{'gameday':1, 'start_time':'14:00', 'end_time':'14:30'},
    #{'gameday':2, 'start_time':'14:00', 'end_time':'15:30'},
    #{'gameday':3, 'start_time':'14:00', 'end_time':'15:30'},
    #{'gameday':5, 'start_time':'14:00', 'end_time':'15:30'}]}
#    {'field_id':18, 'primary':[9,10], 'secondary':None, 'name':'Las Juntas Elem',
#     'start_time':'09:00', 'end_time':'18:00',
#     'unavailable':[{'start':'10/28/13','end':'10/28/13'}]}
]

def getTournDivID(agediv, gender):
    return getDivID(agediv, gender) - 4

def getDivID(agediv, gender):
    if agediv == 'U06':
        if gender == 'B':
            div_id = 1
        else:
            div_id = 2
    elif agediv == 'U08':
        if gender == 'B':
            div_id = 3
        else:
            div_id = 4
    elif agediv == 'U10':
        if gender == 'B':
            div_id = 5
        else:
            div_id = 6
    elif agediv == 'U12':
        if gender == 'B':
            div_id = 7
        else:
            div_id = 8
    elif agediv == 'U14':
        if gender == 'B':
            div_id = 9
        else:
            div_id = 10
    else:
        div_id = 0
    return div_id


_coach_conflict_info = [
        {'coach_id':1, 'conflict':({'agediv':'U06','gender':'B', 'team_id':1},{'agediv':'U08','gender':'B', 'team_id':3})},
        {'coach_id':2, 'conflict':({'agediv':'U08','gender':'G', 'team_id':5},{'agediv':'U10','gender':'G', 'team_id':2})},
        {'coach_id':3, 'conflict':({'agediv':'U08','gender':'G', 'team_id':7},{'agediv':'U08','gender':'B', 'team_id':9})}

]

_team_timeconstraint_info = [
        {'agediv':'U10', 'gender':'G', 'team_id':16,
         'desired':[{'id':1, 'gameday_id':1, 'end_before':'10:30', 'priority':1}]},

        {'agediv':'U12', 'gender':'G', 'team_id':4,
         'desired':[{'id':2, 'gameday_id':5, 'start_after':'13:30', 'priority':1}]},

         {'agediv':'U12', 'gender':'B', 'team_id':1,
         'desired':[{'id':3, 'gameday_id':6, 'start_after':'13:30', 'priority':1}]},

        {'agediv':'U12', 'gender':'G', 'team_id':2,
         'desired':[{'id':4, 'gameday_id':6, 'start_after':'13:30', 'priority':1}]},

        {'agediv':'U12', 'gender':'B', 'team_id':2,
         'desired':[{'id':5, 'gameday_id':7, 'start_after':'13:30', 'priority':1}]},

        {'agediv':'U12', 'gender':'G', 'team_id':3,
         'desired':[{'id':6, 'gameday_id':7, 'start_after':'13:30', 'priority':1}]},

        {'agediv':'U12', 'gender':'B', 'team_id':9,
         'desired':[{'id':7, 'gameday_id':1, 'start_after':'11:30', 'priority':2},
                                {'id':8, 'gameday_id':2, 'start_after':'11:30', 'priority':2},
                                {'id':9, 'gameday_id':3, 'end_before':'12:30','start_after':'15:30', 'priority':2},
                                {'id':10, 'gameday_id':4, 'end_before':'12:30','start_after':'15:00', 'priority':2},
                                {'id':11, 'gameday_id':5, 'end_before':'10:30','start_after':'15:00', 'priority':2},
                                {'id':12, 'gameday_id':6, 'start_after':'11:00', 'priority':2},
                                {'id':13, 'gameday_id':7, 'end_before':'15:30', 'priority':2}]},

        {'agediv':'U10', 'gender':'B', 'team_id':12,
         'desired':[{'id':14, 'gameday_id':1, 'start_after':'11:30', 'priority':2},
                                {'id':15, 'gameday_id':2, 'start_after':'11:30', 'priority':2},
                                {'id':16, 'gameday_id':3, 'end_before':'12:30','start_after':'15:30', 'priority':2},
                                {'id':17, 'gameday_id':4, 'end_before':'12:30','start_after':'15:00', 'priority':2},
                                {'id':18, 'gameday_id':5, 'end_before':'10:30','start_after':'15:00', 'priority':2},
                                {'id':19, 'gameday_id':6, 'start_after':'11:00', 'priority':2},
                                {'id':20, 'gameday_id':7, 'end_before':'15:30', 'priority':2}]},

        {'agediv':'U10', 'gender':'G', 'team_id':3,
         'desired':[{'id':21, 'gameday_id':1, 'start_after':'12:30','priority':3},
                                {'id':22, 'gameday_id':2, 'start_after':'12:30','priority':3},
                                {'id':23, 'gameday_id':3, 'start_after':'12:30','priority':3},
                                {'id':24, 'gameday_id':4, 'start_after':'12:30','priority':3},
                                {'id':25, 'gameday_id':5, 'start_after':'12:30','priority':3},
                                {'id':26, 'gameday_id':6, 'start_after':'12:30','priority':3},
                                {'id':27, 'gameday_id':7, 'start_after':'12:30','priority':3},
                                {'id':28, 'gameday_id':8, 'start_after':'12:30','priority':3},
                                {'id':29, 'gameday_id':9, 'start_after':'12:30','priority':3}]}
]
for team in _team_timeconstraint_info:
        div_id = getDivID(team['agediv'], team['gender'])
        team['div_id'] = div_id

_swap_team_info = [{'agediv':'U12', 'gender':'G', 'team1_id':1, 'team2_id':4},
                                     {'agediv':'U10', 'gender':'B', 'team1_id':16, 'team2_id':3}
                                     ]
for team in _swap_team_info:
        div_id = getDivID(team['agediv'], team['gender'])
        team['div_id'] = div_id

def getLeagueDivInfo():
	# ref http://stackoverflow.com/questions/4573875/python-get-index-of-dictionary-item-in-list
	l_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(_league_div)).get(x)
	return _List_Indexer(_league_div, l_indexerGet)

def getFieldInfo():
	f_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(_field_info)).get(x)
	return _List_Indexer(_field_info, f_indexerGet)

def getTournamentFieldInfo():
    f_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(_tournament_field_info)).get(x)
    return _List_Indexer(_tournament_field_info, f_indexerGet)

def getTeamTimeConstraintInfo(div_id):
        div_team_timeconstraints = [x for x in _team_timeconstraint_info if x['div_id'] == div_id]
        return div_team_timeconstraints

def getSwapTeamInfo(div_id):
        div_swapteaminfo = [x for x in _swap_team_info if x['div_id'] == div_id]
        return div_swapteaminfo

''' create bipartite graph - one column is division, other column is fields
used to define relationship between division and fields
ref http://networkx.github.io/documentation/latest/reference/algorithms.bipartite.html'''
def getDivFieldEdgeWeight_list():
        df_biparG = nx.Graph()
        df_biparG.add_nodes_from([x['div_id'] for x in _league_div], bipartite=0)
        # even through we are using a bipartite graph structure, node names between
        # the column nodes need to be distinct, or else edge (1,2) and (2,1) are not distinguished.
        # instead use edge (1, f2), (2, f1) - use 'f' prefix for field nodes
        df_biparG.add_edges_from([(x['div_id'],'f'+str(y)) for x in _league_div for y in x['fields']])
        div_nodes, field_nodes = bipartite.sets(df_biparG)
        deg_fnodes = {f:df_biparG.degree(f) for f in field_nodes}
        # effective edge sum lists for each division, the sum of the weights of the connected fields;
        # the weights of the associated fields, which are represented as field nodes,
        # are in turn determined by it's degree.  The inverse of the degree for the connected division is
        # taken, which becomes the weight of the particular field associated with the division.  The weights
        # of each field are summed for each division.  The weights also represent the 'total fairness share'
        # of fields associated with a division.
        # Bipartite graph representations, with divisions as one set of nodes, and fields as the other set
        # are used.  Thus a neighbor of a division is always a field.
        edgesum_list = [{'div_id':d, 'edgesum': sum([1.0/deg_fnodes[f] for f in df_biparG.neighbors(d)])}
                                        for d in div_nodes]
        sorted_edgesum_list = sorted(edgesum_list, key=itemgetter('div_id'))
        logging.debug("div fields bipartite graph %s %s effective edge sum for each node %s",
                                    df_biparG.nodes(), df_biparG.edges(), sorted_edgesum_list)

        # depending on the number of teams in each division, the 'fairness share' for each division is adjusted;
        # i.e. a division with more teams is expected to contribute a larger amount to field sharing obligations,
        # such as the number of expected early/late start times for a particular division.  (If one div has 20 teams
        # and the other connected div has only 10 teams, the 20-team division should have a larger share of filling
        # early and late start time games.
        div_indexer = dict((p['div_id'],i) for i,p in enumerate(_league_div))
        # ratio is represented as factor that is multiplied against the 'expected' fair share, which is the 1-inverse
        # of the number of divisions in the connected group - (dividing by the 1-inverse is equiv to multiple by the
        # number of teams - len(connected_list) as shown below)
        divratio_list = [{'div_id':x, 'ratio': len(connected_list)*float(_league_div[div_indexer.get(x)]['totalteams'])/
                                         sum(_league_div[div_indexer.get(y)]['totalteams'] for y in connected_list)}
                                         for connected_list in getConnectedDivisions() for x in connected_list]
        sorted_divratio_list = sorted(divratio_list, key=itemgetter('div_id'))
        # multiply sorted edgesum list elements w. sorted divratio list elements
        # because of the sort all dictionary elements in the list should be sorted according to div_id and obviating
        # need to create an indexerGet function
        # x['div_id'] could have been y['div_id'] in the list comprehension below
        prod_list = [{'div_id': x['div_id'], 'prodratio': x['edgesum']*y['ratio']}
                                 for (x,y) in zip(sorted_edgesum_list, sorted_divratio_list)]
        logging.debug("getDivFieldEdgeWeight: sorted_edge=%s, sorted_ratio=%s, prod=%s",
                                    sorted_edgesum_list, sorted_divratio_list, prod_list)
        # define indexer function object
        prod_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(prod_list)).get(x)
        List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
        return List_Indexer(prod_list, prod_indexerGet)

def getFieldSeasonStatus_list():
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldseason_status_list = []
        for f in _field_info:
                f_id = f['field_id']
                interval_list = []
                numgames_list = []
                for p in f['primary']:
                        divinfo = _league_div[_div_indexer.get(p)]
                        interval_list.append(divinfo['gameinterval'])
                        numgames_list.append(divinfo['gamesperseason'])
                #  if the field has multiple primary divisions, take max of gameinterval and gamesperseason
                interval = max(interval_list)
                gameinterval = timedelta(0,0,0,0,interval)  # convert to datetime compatible obj
                numgamesperseason = max(numgames_list)
                gamestart = parser.parse(f['start_time'])
                end_time = parser.parse(f['end_time'])
                # slotstatus_list has a list of statuses, one for each gameslot
                sstatus_list = []
                while gamestart + gameinterval <= end_time:
                        # for above, correct statement should be adding pure gametime only
                        sstatus_list.append({'start_time':gamestart, 'isgame':False})
                        gamestart += gameinterval
                sstatus_len = len(sstatus_list)
                slotstatus_list = [deepcopy(sstatus_list) for i in range(numgamesperseason)]
                closed_gameday_list = f.get('closed_gameday_list')
                if closed_gameday_list:
                        # if there are fields that are closed on certain days, then slotstatus
                        # entry must be set to null; note gameslotsperday is Not nulled out as the field
                        # applies to the whole season and not individual games.
                        for gameday in closed_gameday_list:
                                slotstatus_list[gameday-1] = None

                fieldseason_status_list.append({'field_id':f['field_id'],
                                                'slotstatus_list':slotstatus_list,
                                                'gameslotsperday':sstatus_len})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldseason_status_list)).get(x)
        List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')
        return List_Indexer(fieldseason_status_list, fstatus_indexerGet)

def getTeamID(agediv, gender, team_id):
        div_id = getDivID(agediv, gender)
        for div in _league_div:
                if div[_id] == div_id:
                        id_range = div['team_id_range']
                        overall_id = id_range[0]+team_id-1
                        break
        else:
                overall_id = False
        return overall_id

def getTournAgeGenderDivision(div_id):
        return getAgeGenderDivision(div_id + 4)

def getAgeGenderDivision(div_id):
        Division = namedtuple('Division', 'age gender')
        if div_id == 1:
                Division.age = 'U06'
                Division.gender = 'B'
        elif div_id == 2:
                Division.age = 'U06'
                Division.gender = 'G'
        elif div_id == 3:
                Division.age = 'U08'
                Division.gender = 'B'
        elif div_id == 4:
                Division.age = 'U08'
                Division.gender = 'G'
        elif div_id == 5:
                Division.age = 'U10'
                Division.gender = 'B'
        elif div_id == 6:
                Division.age = 'U10'
                Division.gender = 'G'
        elif div_id == 7:
                Division.age = 'U12'
                Division.gender = 'B'
        elif div_id == 8:
                Division.age = 'U12'
                Division.gender = 'G'
        elif div_id == 9:
                Division.age = 'U14'
                Division.gender = 'B'
        elif div_id == 10:
                Division.age = 'U14'
                Division.gender = 'G'
        else:
                Division.age = 'NA'
                Division.gender = 'NA'
        return Division

def getDivisionData(div_id):
        div_indexer = dict((p['div_id'],i) for i,p in enumerate(_league_div))
        index = div_indexer.get(div_id)
        division = _league_div[index]
        return division

_gameday_to_cal = {1:'Sept 7', 2:'Sept 14', 3:'Sept 21', 4:'Sept 28', 5:'Oct 5',
                                     6:'Oct 12', 7:'Oct 19', 8:'Oct 26', 9:'Nov 2', 10:'Nov 9',
                                     11:'Nov 16', 12:'Nov 23'}
_gameday_to_numericalcal = {1:'9/7/2013', 2:'9/14/2013', 3:'9/21/2013', 4:'9/28/2013', 5:'10/5/2013',
                                                        6:'10/12/2013', 7:'10/19/2013', 8:'10/26/2013', 9:'11/2/2013', 10:'11/9/2013',
                                                        11:'11/16/2013', 12:'11/23/2013'}

_tourngameday_to_numericalcal = {1:'10/26/2013', 2:'10/27/2013', 3:'11/2/2013', 4:'11/3/2013', 5:'11/9/2013', 6:'11/10/2013'}
_tourngameday_to_date = {1:'Saturday',2:'Sunday',3:'Saturday',4:'Sunday',5:'Saturday',6 :'Sunday'}
def mapGamedayIdToCalendar(gameday_id, format=0):
        calformat = _gameday_to_cal.get(gameday_id) if format == 0 else _gameday_to_numericalcal.get(gameday_id)
        return calformat

def tournMapGamedayIdToCalendar(gameday_id):
    return _tourngameday_to_numericalcal.get(gameday_id)
def tournMapGamedayIdToDate(gameday_id):
    return _tourngameday_to_date.get(gameday_id)

#find inter-related divisions through the field_info list
# this should be simplier than the method below whith utilize the division info list
def getConnectedDivisions():
        G = nx.Graph()
        for field in _field_info:
                prev_node = None
                for div_id in field['primary']:
                        if not G.has_node(div_id):
                                G.add_node(div_id)
                        if prev_node is not None and not G.has_edge(prev_node, div_id):
                                G.add_edge(prev_node, div_id)
                        prev_node = div_id
        connected_div_components = connected_components(G)
        #serialize field-connected divisions as graph and save it
        #(instead of saving list of connected components); used by leaguediv_process to
        #determine schedule allocation of connected divisions
        #connected_graph = json_graph.node_link_data(G)
        return connected_div_components

# create coach conflict graph to find conflict metrics
conflictG = nx.Graph()
for coach in _coach_conflict_info:
        prev_node = None
        for team in coach['conflict']:
                a = team['agediv']
                g = team['gender']
                div_id = getDivID(a,g)
                if not conflictG.has_node(div_id):
                        conflictG.add_node(div_id)
                if prev_node is not None:
                        if not conflictG.has_edge(prev_node, div_id):
                                conflictG.add_edge(prev_node, div_id, weight=1.0)
                        else:
                                # if edge already exists, increase weight
                                conflictG.edge[prev_node][div_id]['weight'] += 1
                prev_node = div_id
# for printing edge attributes
# http://networkx.github.io/documentation/latest/reference/classes.graph.html#overview
a = [ (u,v,edata['weight']) for u,v,edata in conflictG.edges(data=True) if 'weight' in edata ]
print a

jsonstr = json.dumps({"creation_time":time.asctime(),
                                            "leaguedivinfo":_league_div,
                                            "conflict_info":_coach_conflict_info,
                                            "field_info":_field_info})
f = open('leaguediv_json.txt','w')
f.write(jsonstr)

f.close()
