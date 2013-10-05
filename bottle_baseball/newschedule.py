#!/usr/bin/python
''' Copyright YukonTR 2013 '''
from dbinterface import MongoDBInterface
import simplejson as json

class NewSchedule:
    def __init__(self, mongoClient, db_name, divinfo_str):
        divinfo_dict = json.loads(divinfo_str)
        for division in divinfo_dict:
            print division
