''' Copyright YukonTR 2013 '''

from schedule_util import getConnectedDivisionGroup
from itertools import groupby, cycle
from operator import itemgetter
from schedule_util import roundrobin
from datetime import timedelta
from dateutil import parser
from copy import deepcopy
from collections import namedtuple
import logging
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

class TournamentFieldTimeScheduler:
    def __init__(self, tdbinterface, tfield_tuple, divinfo, dindexerGet):
        self.tdbInterface = tdbinterface
        self.tfieldinfo_list = tfield_tuple.dict_list
        self.tfindexerGet = tfield_tuple.indexerGet
        self.connected_div_components = getConnectedDivisionGroup(self.tfieldinfo_list)
        self.divinfo_list = divinfo
        self.dindexerGet = dindexerGet
        tfstatus_tuple = self.getTournFieldSeasonStatus_list()
        self.tfstatus_list = tfstatus_tuple.dict_list
        self.tfindexerGet = tfstatus_tuple.indexerGet
        for tfield in self.tfieldinfo_list:
            f_id = tfield['field_id']
            for d_id in tfield['primary']:
                index = self.dindexerGet(d_id)
                if index is not None:
                    division = self.divinfo_list[index]
                    # check existence of key 'fields' - if it exists, append to list of fields, if not create
                    if 'fields' in division:
                        division['fields'].append(f_id)
                    else:
                        division['fields'] = [f_id]

    def generateSchedule(self, totalmatch_list):
        tmindexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(totalmatch_list)).get(x)
        self.tdbInterface.dbInterface.dropGameDocuments()  # reset game schedule docs
        for connected_div_list in self.connected_div_components:
            # get the list of divisions that make up a connected component.
            # then get the matchlist corresponding to the connected divisions
            connecteddiv_match_list = [totalmatch_list[tmindexerGet(x)] for x in connected_div_list]
            #print 'connectedmatch', connecteddiv_match_list
            # flatten out the list embed div_id value in each dictionary
            # also flatten out 'GAME_TEAM' list generate by the match generator
            flatmatch_list = [{'ROUND_ID':z['ROUND_ID'], 'HOME':p['HOME'], 'AWAY':p['AWAY'], 'DIV_ID':x['div_id']} for x in connecteddiv_match_list for y in x['match_list'] for z in y for p in z['GAME_TEAM']]
            # sort the list according to round_id (needed for groupby below), and then by div_id
            sorted_flatmatch_list = sorted(flatmatch_list, key=itemgetter('ROUND_ID', 'DIV_ID'))
            # group list by round_id; dict value of 'match_list' key is a nested array, which is created by an inner groupby based on div_id
            # The nested list will be passed to the roundrobin multiplexer
            #for key, items in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID')):
            #   for key1, items1 in groupby(items, key=itemgetter('DIV_ID')):
            #      for j in items1:
            #         print key, key1, j
            grouped_match_list = [{'round_id':rkey, 'match_list':[[{'home':x['HOME'], 'away':x['AWAY'], 'div_id':dkey} for x in ditems] for dkey, ditems in groupby(ritems, key=itemgetter('DIV_ID'))]} for rkey, ritems in groupby(sorted_flatmatch_list, key=itemgetter('ROUND_ID'))]
            logging.debug("tournftscheduler:gensched:groupedlist=%s", grouped_match_list)
            #find the fields available for the connected_div_set by finding
            # the union of fields for each div
            fieldset = reduce(set.union,
                              map(set,[self.divinfo_list[self.dindexerGet(x)]['fields'] for x in connected_div_list]))
            print 'fieldset', fieldset
            field_cycle = cycle(fieldset)
            current_gameday = 1
            self.findNextEarliestFieldSlot(list(fieldset), current_gameday)
            for round_games in grouped_match_list:
                round_id = round_games['round_id']
                rrgenobj = roundrobin(round_games['match_list'])
                for rrgame in rrgenobj:
                    rrfield_id = field_cycle.next()
                    print round_id, rrgame, rrfield_id

    def getTournFieldSeasonStatus_list(self):
        # routine to return initialized list of field status slots -
        # which are all initially set to False
        # each entry of list is a dictionary with two elemnts - (1)field_id
        # (2) - two dimensional matrix of True/False status (outer dimension is
        # round_id, inner dimenstion is time slot)
        fieldseason_status_list = []
        for f in self.tfieldinfo_list:
            f_id = f['field_id']
            numgamedays = f['numgamedays']
            gamestart = parser.parse(f['start_time'])
            end_time = parser.parse(f['end_time'])
            ginterval_list = []
            rrgamedays_list = []
            for p in f['primary']:
                divinfo = self.divinfo_list[self.dindexerGet(p)]
                ginterval_list.append(int(divinfo['gameinterval']))
                rrgamedays_list.append(int(divinfo['rr_gamedays']))
            # take max for now - this is a simplification
            # default for phmsa is that divisions that share a field have
            # same game intervals
            ginterval = max(ginterval_list)
            rrgamedays = max(rrgamedays_list)
            # convert to datetime compatible obj
            gameinterval = timedelta(0,0,0,0,ginterval)
            # slotstatus_list has a list of statuses, one for each gameslot
            # create game status list for default start/end time days
            sstatus_list = []
            while gamestart + gameinterval <= end_time:
                # for above, correct statement should be adding pure gametime only
                sstatus_list.append({'start_time':gamestart, 'isgame':False})
                gamestart += gameinterval

            # find gamedays with different field availability times
            ldays_list = f.get('limiteddays')
            if ldays_list:
                lallstatus_list = []
                for lday in ldays_list:
                    lgameday = lday['gameday']
                    lgamestart = parser.parse(lday['start_time'])
                    lgameend = parser.parse(lday['end_time'])
                    lstatus_list = []
                    while lgamestart + gameinterval <= lgameend:
                        lstatus_list.append({'start_time':lgamestart,
                                            'isgame':False})
                        lgamestart += gameinterval
                    lallstatus_list.append({'lgameday':lgameday,
                                           'lstatus_list':lstatus_list})
                lindexerGet = lambda x: dict((p['lgameday'],i) for i,p in enumerate(lallstatus_list)).get(x)

            # find gamedays w closed field
            closed_list = f.get('closed_gameday_list')
            # assign appropriate slotsstatus list for each gameday
            # for current field_id
            slotstatus_list = numgamedays*[None] #initialize
            for gameday in range(1,numgamedays+1):
                if closed_list and gameday in closed_list:
                    # leave slotstatus_list entry as None
                    continue
                elif ldays_list and lindexerGet(gameday):
                    lindex = lindexerGet(gameday)
                    # decrement index by one from gameday value as gameday is
                    # 1-indexed
                    slotstatus_list[gameday-1] = lallstatus_list[lindex]['lstatus_list']
                else:
                    slotstatus_list[gameday-1] = deepcopy(sstatus_list)

            fieldseason_status_list.append({'field_id':f['field_id'],
                                            'slotstatus_list':slotstatus_list,
                                            'rrgamedays':rrgamedays})
        fstatus_indexerGet = lambda x: dict((p['field_id'],i) for i,p in enumerate(fieldseason_status_list)).get(x)
        return _List_Indexer(fieldseason_status_list, fstatus_indexerGet)

    def findNextEarliestFieldSlot(self, field_list, cur_gameday):
        field_cycle = cycle(field_list)
        isgame_list = [(f,
                         self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday])
                        for f in field_list]
        print 'isgame', isgame_list
        mintime_list = [(f,
                         min(self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday], key=itemgetter('start_time')))
                        for f in field_list]
        print 'mintime', mintime_list
#        for f in field_list:
#            sstatus = self.tfstatus_list[self.tfindexerGet(f)]['slotstatus_list'][cur_gameday]
#            if sstatus:
#                mintime = min(sstatus,key=itemgetter('start_time'))
#                print 'f mintime', f, mintime
