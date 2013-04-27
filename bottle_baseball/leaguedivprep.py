#!/usr/bin/python
import simplejson as json

league_div = [
{ '_id':1, 'agediv':'U6', 'gender':'B', 'totalteams':25,
  'totalfields':2, 'gamedaysperweek':1},
{ '_id':2, 'agediv':'U6', 'gender':'G', 'totalteams':20,
  'totalfields':2, 'gamedaysperweek':1},
{ '_id':3, 'agediv':'U8', 'gender':'B', 'totalteams':35,
  'totalfields':4, 'gamedaysperweek':1},
{ '_id':4, 'agediv':'U8', 'gender':'G', 'totalteams':30,
  'totalfields':4, 'gamedaysperweek':1},
{ '_id':5, 'agediv':'U10', 'gender':'B', 'totalteams':34,
  'totalfields':4, 'gamedaysperweek':2},
{ '_id':6, 'agediv':'U10', 'gender':'G', 'totalteams':38,
  'totalfields':4, 'gamedaysperweek':2}
]

jsonstr = json.dumps(league_div)
f = open('leaguediv_json.txt','w')
f.write(jsonstr)
f.close()
