''' Copyright YukonTR 2014 '''
import logging
from operator import itemgetter

_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class ConflictProcess(object):
    def __init__(self, conflictinfo_list, prefinfo_list):
        self.conflictinfo_list = conflictinfo_list
        self.prefinfo_list = prefinfo_list
        self.cindexerMatch = lambda x: [i for i,p in
            enumerate(self.conflictinfo_list) if p['div_1_id']==x or
            p['div_2_id']==x]

    def process(cdiv_list):
        for div_id in cdiv_list:
            index_list = self.cindexerMatch(div_id)
            conflict_list = [self.conflictinfo_list[index]
                for index in index_list]

    '''
    @property
    def tminfo_list(self):
        return self._tminfo_list

    @tminfo_list.setter
    def tminfo_list(self, value):
        self._tminfo_list = value

    @property
    def tminfo_indexerGet(self):
        return self._tminfo_indexerGet

    @tminfo_indexerGet.setter
    def tminfo_indexerGet(self, value):
        self._tminfo_indexerGet = value

    @property
    def tminfo_indexerMatch(self):
        return self._tminfo_indexerMatch

    @tminfo_indexerMatch.setter
    def tminfo_indexerMatch(self, value):
        self._tminfo_indexerMatch = value
    '''

