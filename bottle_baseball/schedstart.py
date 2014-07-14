#!/usr/local/bin/python2.7
# Copyright YukonTR 2013
from bottle import route, request, run
#ref http://simplejson.readthedocs.org/en/latest/
import simplejson as json
import sys, socket
import time
import logging
from leaguediv_process import *

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    now = time.strftime("%c")
    logging.debug("Current time is %s",now)
    logging.debug("Version: 0.0.0.4c")
    if socket.gethostname() == 'web380.webfaction.com':
        run(port = 31032, server = 'cherrypy')
#        run(host='localhost',port = 31032)  # check webfaction port setting
    else:
        run(host='localhost', port=8080, debug=True)

if __name__ == '__main__':
    main()
