#!/usr/bin/python
from leaguedivprep import getDivFieldEdgeWeight_list
import logging

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    getDivFieldEdgeWeight_list()

if __name__ == '__main__':
    main()
