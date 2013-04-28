#!/usr/bin/python
import simplejson as json

fname = 'leaguediv_json.txt'
json_file = open(fname)
ldata = json.load(json_file)
pprint(data)
json_file.close()

'''
references
http://www.tutorial.useiis7.net/dojodoc/001/
http://myadventuresincoding.wordpress.com/2011/01/02/creating-a-rest-api-in-python-using-bottle-and-mongodb/
http://gotofritz.net/blog/weekly-challenge/restful-python-api-bottle/
http://bottlepy.org/docs/dev/tutorial.html#request-routing
'''
@route('/schedule/<sid>', method='GET')
def get_schedule(tid=None):
    if tid is None:
        return ldata
    for div in ldata:
        if div[_id] == tid:
            return div



