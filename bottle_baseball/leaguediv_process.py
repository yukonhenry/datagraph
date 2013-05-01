#!/usr/bin/python
import simplejson as json
from pprint import pprint
from bottle import route, request
from scheduler import generateRRSchedule

fname = 'leaguediv_json.txt'
json_file = open(fname)
ldata = json.load(json_file)
pprint(ldata)
json_file.close()

'''
references
http://www.tutorial.useiis7.net/dojodoc/001/
http://myadventuresincoding.wordpress.com/2011/01/02/creating-a-rest-api-in-python-using-bottle-and-mongodb/
http://gotofritz.net/blog/weekly-challenge/restful-python-api-bottle/
http://bottlepy.org/docs/dev/tutorial.html#request-routing
'''
@route('/leaguedivinfo')
def leaguedivinfo_all():
    callback_name = request.query.callback
    a = json.dumps(ldata)
    return callback_name+'('+a+')'

@route('/leaguedivinfo/<tid:int>', method='GET')
def leaguedivinfo(tid):
    callback_name = request.query.callback
    ldata_divinfo = ldata['leaguedivinfo']
    for div in ldata_divinfo:
        if div['_id'] == tid:
            nt = div['totalteams']
            nv = div['totalfields']
            game_list = generateRRSchedule(nt, nv)
            a = json.dumps({"game_list":game_list})
            return callback_name+'('+a+')'
    else:
        return False
