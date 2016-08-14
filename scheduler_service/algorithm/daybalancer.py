from operator import itemgetter
from itertools import groupby
from functools import reduce
from math import sqrt
import random
from copy import deepcopy
from util.sched_exceptions import CodeLogicError
import pdb
class DayBalancer(object):
    def __init__(self, divinfo_tuple, fieldinfo_tuple, fstatus_tuple):
        self.divinfo_list = divinfo_tuple.dict_list
        self.dindexerGet = divinfo_tuple.indexerGet
        self.fieldinfo_list = fieldinfo_tuple.dict_list
        self.findexerGet = fieldinfo_tuple.indexerGet
        self.fieldstatus_list = fstatus_tuple.dict_list
        self.fstatus_indexerGet = fstatus_tuple.indexerGet

        self.day_counters = self.initialize_counters(self.divinfo_list, self.dindexerGet, self.fieldinfo_list,
                                                     self.findexerGet)

    def initialize_counters(self, divinfo_list, dindexerGet, fieldinfo_list,
                            findexerGet):
        counters = []
        for divinfo in divinfo_list:
            div_id = divinfo['div_id']
            div_field_days = set()
            for field_id in divinfo['divfield_list']:
                days = fieldinfo_list[findexerGet(field_id)]['dayweek_list']
                div_field_days.update(days)
            targets = self.initialize_targets(divinfo, div_field_days)
            day_counters = [{'count':0, 'day_id': x['day_id'], 'target': x['target'],
                             'primary': x['primary'], 'secondary': x['secondary']} for x in targets]
            counters.append({'div_id': div_id, 'day_counters': day_counters})
        return counters

    def initialize_targets(self, divinfo, div_field_days):
        total_div_games = divinfo['totalgamedays'] * divinfo['totalteams'] / 2
        if 'primary_days' in divinfo:
            primary_days = divinfo['primary_days']
            if 'secondary_days' in divinfo and divinfo['secondary_days']:
                secondary_days = divinfo['secondary_days']
                fair_games_per_day = total_div_games / (len(div_field_days) - len(primary_days))
            else:
                secondary_days = None
                fair_games_per_day = 0
            secondary_state = lambda x: True if secondary_days and x in secondary_days else False
            div_games_per_day = total_div_games / len(primary_days)
            targets = [{'day_id':x, 'target': div_games_per_day, 'primary': True,
                        'secondary': secondary_state(x)}
                       if x in primary_days else {'day_id': x,
                                                  'target': total_div_games / len(secondary_days) if secondary_state(x) else fair_games_per_day,
                                                  'primary': False,
                                                  'secondary': secondary_state(x)}
                       for x in div_field_days]
        else:
            div_games_per_day = total_div_games / len(div_field_days)
            targets = [{'day_id':x, 'target': div_games_per_day, 'primary': True, 'secondary': False}
                       for x in div_field_days]
        return targets

    def get_divday_counter(self, div_id, game_day_id):
        div_day_counters = [y for x in self.day_counters for y in x['day_counters']
                            if x['div_id'] == div_id and y['day_id'] == game_day_id]
        if not div_day_counters:
            raise CodeLogicError("DayBalacer: counter does not exist for div %d day %d" % (div_id, game_day_id))
        else:
            return div_day_counters[0]

    def update_counters(self, div_id, game_date):
        game_day_id = game_date.weekday()
        div_day_counter = self.get_divday_counter(div_id, game_day_id)
        div_day_counter['count'] += 1
        return div_day_counter

    def assign_prefdays_priorities(self, div_id, datesortedfields):
        earliest_date = datesortedfields[0]['date']
        for date_field in datesortedfields:
            week_id = (date_field['date'] - earliest_date).days // 7
            weekday_id = date_field['date'].weekday()
            divday_counter = self.get_divday_counter(div_id, weekday_id)
            if divday_counter['primary']:
                date_field.update({'priority': 1, 'week_id': week_id})
            elif divday_counter['secondary']:
                date_field.update({'priority': 2, 'week_id': week_id})
            else:
                date_field.update({'priority': 3, 'week_id': week_id})
        return sorted(datesortedfields, key=itemgetter('week_id', 'priority', 'date'))

    def ReDayBalance(self, fieldset, connected_divs):
        pass
