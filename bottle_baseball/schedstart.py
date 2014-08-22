#!/usr/local/bin/python2.7
# Copyright YukonTR 2013
from bottle import route, request, run
import sys, socket
import time
import logging
from leaguediv_process import *

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    now = time.strftime("%c")
    logging.debug("Current time is %s",now)
    logging.debug("Version: 0.0.0.10b")
    if socket.gethostname() == 'web380.webfaction.com':
        run(port = 31032, server = 'cherrypy')
    else:
        run(host='localhost', port=8080, debug=True)

if __name__ == '__main__':
    main()
