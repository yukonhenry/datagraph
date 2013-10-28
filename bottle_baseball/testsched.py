#!/usr/bin/python
from leaguedivprep import getDivFieldEdgeWeight_list
from schedule_util import nth_listitem
from leaguediv_process import elimination2013, export_elim2013, get_alldivSchedule
import logging

def main():
    logging.basicConfig(filename='debug.log', filemode='w', level=logging.INFO)
    #logging.basicConfig(level=logging.INFO)
    '''
    l = [0,0,1,0,1,0,1]
    for i in range(6):
        print l, i, nth_listitem(l,1,i)
    '''
    get_alldivSchedule()
    #elimination2013('phmsacup2013')
    #export_elim2013('phmsacup2013')
if __name__ == '__main__':
    main()
