#!/usr/bin/python
from leaguedivprep import getDivFieldRelation_graph
import logging

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    getDivFieldRelation_graph()

if __name__ == '__main__':
    main()
