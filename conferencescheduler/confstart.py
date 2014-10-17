#!/usr/local/bin/python2.7
import time
import logging
from scheduler import confsched

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    now = time.strftime("%c")
    logging.debug("Current time is %s",now)
    confsched()
    '''
    logging.debug("Version: 0.0.0.13p")
    if socket.gethostname() == 'web380.webfaction.com':
        run(port = 31032, server = 'cherrypy')
    else:
        run(host='localhost', port=8080, debug=True)
    '''

if __name__ == '__main__':
    main()
