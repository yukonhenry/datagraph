#!/usr/bin/python
from singletonlite import mongoClient
from schedmaster import SchedMaster
import logging

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)
    '''
    l = [0,0,1,0,1,0,1]
    for i in range(6):
        print l, i, nth_listitem(l,1,i)
    '''
    #get_alldivSchedule()
    #elimination2013('phmsacup2013')
    #export_elim2013('phmsacup2013')
    schedMaster = SchedMaster(mongoClient, "rrdb", "ph", "PHMSA",
        "M2014")
    dbstatus = schedMaster.generate()
if __name__ == '__main__':
    main()
