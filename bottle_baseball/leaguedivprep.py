#!/usr/bin/python
import simplejson as json
import time
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
  'gamedaysperweek':2, 'gameinterval':75}
]

jsonstr = json.dumps({"creation_time":time.asctime(),
                      "leaguedivinfo":league_div})
f = open('leaguediv_json.txt','w')
f.write(jsonstr)
f.close()
