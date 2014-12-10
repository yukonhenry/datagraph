#!/usr/bin/python
''' Copyright YukonTR 2013 '''
# singleton effects by utilizing module import
# ref http://stackoverflow.com/questions/10936709/why-does-a-python-module-act-like-a-singleton
import socket
from pymongo import MongoClient
from db.dbinterface import MongoDBInterface
from time import asctime

if socket.gethostname() == 'web380.webfaction.com':
    mongoClient = MongoClient('localhost', 11466)
    hostserver = "webfaction"
else:
    mongoClient = MongoClient()
    hostserver = "local"
generic_dbInterface = MongoDBInterface(mongoClient)
creation_time = asctime()
