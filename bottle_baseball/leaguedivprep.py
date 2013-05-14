#!/usr/bin/python
import simplejson as json
import time
import networkx as nx
from networkx import connected_components
from networkx.readwrite import json_graph
league_div = [
{ '_id':1, 'agediv':'U6', 'gender':'B', 'totalteams':25,
  'fields':[0,1],
  'gamedaysperweek':1, 'gameinterval':50},
{ '_id':2, 'agediv':'U6', 'gender':'G', 'totalteams':20,
  'fields':[0,1],
  'gamedaysperweek':1, 'gameinterval':50},
{ '_id':3, 'agediv':'U8', 'gender':'B', 'totalteams':35,
  'fields':[2,3,4],
  'gamedaysperweek':1, 'gameinterval':60},
{ '_id':4, 'agediv':'U8', 'gender':'G', 'totalteams':30,
  'fields':[2,3,4],
  'gamedaysperweek':1, 'gameinterval':60},
{ '_id':5, 'agediv':'U10', 'gender':'B', 'totalteams':34,
  'fields':[5,6,7],
  'gamedaysperweek':2, 'gameinterval':75},
{ '_id':6, 'agediv':'U10', 'gender':'G', 'totalteams':38,
  'fields':[5,6,7],
  'gamedaysperweek':2, 'gameinterval':75},
{ '_id':7, 'agediv':'U12', 'gender':'B', 'totalteams':8,
  'fields':[8,9,10],
  'gamedaysperweek':2, 'gameinterval':90},
{ '_id':8, 'agediv':'U12', 'gender':'G', 'totalteams':4,
  'fields':[8,9,10],
  'gamedaysperweek':2, 'gameinterval':90}
]
field_info = [
    {'_id':1, 'age_group_main':['U6'], 'age_group_backup':['U8']},
    {'_id':2, 'age_group_main':['U6'], 'age_group_backup':['U8']},
    {'_id':3, 'age_group_main':['U8'], 'age_group_backup':['U6']},
    {'_id':4, 'age_group_main':['U8'], 'age_group_backup':['U6']},
    {'_id':5, 'age_group_main':['U8'], 'age_group_backup':['U6']},
    {'_id':6, 'age_group_main':['U10'], 'age_group_backup':['U12']},
    {'_id':7, 'age_group_main':['U10'], 'age_group_backup':['U12']},
    {'_id':8, 'age_group_main':['U10'], 'age_group_backup':['U12']},
    {'_id':9, 'age_group_main':['U12'], 'age_group_backup':None},
    {'_id':10, 'age_group_main':['U12'], 'age_group_backup':None},
    {'_id':11, 'age_group_main':['U12'], 'age_group_backup':None}
]
coach_conflict_info = [
    {'coach_id':1, 'conflict':({'agediv':'U6','gender':'B', 'team_id':1},{'agediv':'U8','gender':'B', 'team_id':3})}
]

# using networkx
G = nx.Graph()
index = 0
# find inter-related divsions by finding out if there are fields
# that are shared between divisions.
# To discover shared fields, do intersection of sets using  set(array1).intersection(array2)
max_index = len(league_div)-1
# loop through each division in division list
for division in league_div:
    div_id = division['_id']
    G.add_node(div_id)
    field_set = set(division['fields'])
    # and do set intersection with other divisions
    # only need to do set intersection with 'remaining' divisions
    for other_div in league_div[index+1:]:
        if field_set.intersection(other_div['fields']):
            G.add_edge(div_id, other_div['_id'])
    index += 1
#data = json_graph.node_link_data(G)
connected_list = connected_components(G)
print connected_list
jsonstr = json.dumps({"creation_time":time.asctime(),
                      "leaguedivinfo":league_div,
                      "conflict_info":coach_conflict_info,
                      "connected_divisions":connected_list,
                      "field_info":field_info})
f = open('leaguediv_json.txt','w')
f.write(jsonstr)

f.close()
