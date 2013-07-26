#!/usr/bin/python
from leaguedivprep import getDivFieldEdgeWeight_list
import logging

def main():
    #logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    list_indexer = getDivFieldEdgeWeight_list()
    logging.debug("list=%s index=%d dict=%s",
                  list_indexer.dict_list, list_indexer.indexerGet(1),list_indexer.dict_list[list_indexer.indexerGet(1)])

if __name__ == '__main__':
    main()
