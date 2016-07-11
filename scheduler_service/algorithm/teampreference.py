import pdb
from operator import itemgetter
from itertools import groupby
from functools import reduce
from math import sqrt
import random
from copy import deepcopy
from util.sched_exceptions import CodeLogicError
PRIORITY_RATIOS = [0.9, 0.7, 0.5, 0.3]
PRIORITY_WEIGHTS = {1: 10, 2: 5, 3: 3, 4: 1}
def process_tmprefdays(prefdays_tuple, divinfo_tuple, fieldinfo_tuple, fieldstatus_tuple, sched_tuple):
    divinfo_list = divinfo_tuple.dict_list
    divinfo_indexerGet = divinfo_tuple.indexerGet
    prefdays_list = prefdays_tuple.dict_list
    prefdays_list.sort(key=itemgetter('priority'))
    divteam_metrics = calculate_initial_divteam_metrics(prefdays_list, prefdays_tuple.indexerGet,
                                                  divinfo_list, divinfo_indexerGet,
                                                  sched_tuple, fieldinfo_tuple)
    for priority, priority_group in groupby(prefdays_list, key=itemgetter('priority')):
        priority_list = list(priority_group)
        random.shuffle(priority_list)
        for team_priority_config in priority_list:
            team_metrics = get_team_metrics(divteam_metrics, team_priority_config['div_id'],
                                            team_priority_config['tm_id'])
            if team_metrics['preference_ratio'] >= team_metrics['preference_target']:
                continue
            apply_team_preference(team_priority_config, team_metrics,
                                  divteam_metrics, fieldstatus_tuple, prefdays_list)

def get_team_metrics(divteam_metrics, div_id, team_id):
    return (t for d in divteam_metrics for t in d['team_data']
                    if d['div_id'] == div_id and t['team_id'] == team_id).next()

def find_prefdays_for_team(prefdays_list, div_id, team_id):
    prefdays = [x['prefdays'] for x in prefdays_list if x['div_id'] == div_id and x['tm_id'] == team_id]
    if prefdays:
        return prefdays[0]
    else:
        return None

def apply_team_preference(team_config, team_metrics, divteam_metrics, fieldstatus_tuple,
                          prefdays_list):
    pref_unmet_schedule_for_team = [x for x in team_metrics['schedule']
                                    if x['game_date'].weekday() not in team_config['prefdays']]
    for pref_unmet_sched in pref_unmet_schedule_for_team:
        best_swap = find_best_swap_candidate(team_config, pref_unmet_sched, team_metrics, divteam_metrics,
                                             prefdays_list)
        swap_out_unmet(best_swap, pref_unmet_sched, fieldstatus_tuple)

def swap_out_unmet(best_swap, pref_unmet, fieldstatus_tuple):
    pass

def find_best_swap_candidate(team_config, pref_unmet_sched, team_metrics, divteam_metrics, prefdays_list):
    candidates = find_swap_candidates(team_config, pref_unmet_sched, divteam_metrics)
    costs = []
    for candidate in candidates:
        cost = calculate_cost_after_emulated_swap(candidate, team_config, pref_unmet_sched, team_metrics,
                                                  divteam_metrics, prefdays_list)
        costs.append({'cost': cost, 'candidate': candidate})
    min_cost = min(costs, key=itemgetter('cost'))['cost']
    min_cost_candidates = [x['candidate'] for x in costs if x['cost'] == min_cost]
    if len(min_cost_candidates) == 1:
        return min_cost_candidates[0]
    else:
        return min(min_cost_candidates, key=lambda x: x['swap_sched']['game_date'])

def find_opponent_metrics(team_config, pref_unmet, divteam_metrics):
    div_id = team_config['div_id']
    opponent_id = pref_unmet['away_id'] if team_config['tm_id'] == pref_unmet['home_id'] else pref_unmet['home_id']
    opponent_metrics = get_team_metrics(divteam_metrics, div_id, opponent_id)
    return opponent_metrics

def calculate_cost_after_emulated_swap(candidate, team_config, pref_unmet_sched, team_metrics,
                                       divteam_metrics, prefdays_list):
    costs = calculate_team_costs(candidate, team_config, pref_unmet_sched, team_metrics,
                                 divteam_metrics, prefdays_list)
    aggregate_cost = sum(x['cost']*PRIORITY_WEIGHTS[x['priority']] for x in costs)
    return aggregate_cost

def calculate_team_costs(candidate, team_config, pref_unmet_sched, team_metrics,
                         divteam_metrics, prefdays_list):
    team_cost = {'cost': find_prefteam_swap_cost(team_metrics, 1),
                 'priority': team_metrics['priority'], 'type': 'team'}
    candidate_swap_day = candidate['swap_sched']['game_date'].weekday()
    pref_unmet_swap_day = pref_unmet_sched['game_date'].weekday()
    opponent_cost = calculate_opponent_team_cost(candidate, team_config, pref_unmet_sched,
                                                 divteam_metrics, prefdays_list, candidate_swap_day, pref_unmet_swap_day)
    swap_home_cost = calculate_swap_team_cost(candidate, divteam_metrics, prefdays_list,
                                              candidate_swap_day, pref_unmet_swap_day, 'home_id')
    swap_away_cost = calculate_swap_team_cost(candidate, divteam_metrics, prefdays_list,
                                              candidate_swap_day, pref_unmet_swap_day, 'away_id')
    return [team_cost, opponent_cost, swap_home_cost, swap_away_cost]

def calculate_opponent_team_cost(candidate, team_config, pref_unmet_sched, divteam_metrics,
                                 prefdays_list, candidate_swap_day, unmet_swap_day):
    opponent_metrics = find_opponent_metrics(team_config, pref_unmet_sched, divteam_metrics)
    opponent_cost = find_swap_cost(opponent_metrics, prefdays_list, candidate_swap_day,
                                   unmet_swap_day, 'candidate_to_pref')
    return {'cost': opponent_cost, 'priority': opponent_metrics['priority'], 'type': 'opposite'}

def calculate_swap_team_cost(candidate, divteam_metrics, prefdays_list, candidate_swap_day,
                             unmet_swap_day, team_type):
    swap_metrics = get_team_metrics(divteam_metrics, candidate['div_id'],
                                    candidate['swap_sched'][team_type])
    swap_cost = find_swap_cost(swap_metrics, prefdays_list, candidate_swap_day,
                               unmet_swap_day, 'candidate_from_pref')
    return {'cost': swap_cost, 'priority': swap_metrics['priority'], 'type': team_type}

def find_swap_cost(metrics, prefdays_list, candidate_day, unmet_swap_day, swap_type):
    if metrics['ratio_type'] == 'preference':
        return find_preference_swap_cost(metrics, prefdays_list, candidate_day, unmet_swap_day,
                                         swap_type)
    else:
        return find_fairness_swap_cost(metrics, candidate_day, unmet_swap_day)

def find_preference_swap_cost(metrics, prefdays_list, candidate_day, unmet_swap_day, swap_type):
    candidate_true_increment = 1 if swap_type == 'candidate_to_pref' else -1
    prefdays = find_prefdays_for_team(prefdays_list, metrics['div_id'], metrics['team_id'])
    if prefdays is None:
        raise CodeLogicError("teampreference:find_swap_cost:prefday inconsistent %s" % (metrics,))
    else:
        swap_out_condition = unmet_swap_day in prefdays
        candidate_condition = candidate_day in prefdays
        if swap_out_condition != candidate_condition:
            if candidate_condition:
                cost = find_prefteam_swap_cost(metrics, candidate_true_increment)
            else:
                cost = find_prefteam_swap_cost(metrics, -candidate_true_increment)
        else:
            cost = metrics['preference_cost'] # unchanged cost
        return cost

def find_prefteam_swap_cost(metrics, increment_value):
    emulated_satisfied_ount = metrics['preference_satisfied_count'] + increment_value
    emulated_ratio = float(emulated_satisfied_ount) / metrics['totalgames']
    return metrics['preference_target'] - emulated_ratio

def find_fairness_swap_cost(metrics, candidate_day, unmet_swap_day):
    emulated_counters = deepcopy(metrics['counters'])
    increment_count_for_day(emulated_counters, unmet_swap_day, -1)
    increment_count_for_day(emulated_counters, candidate_day, 1)
    fairness_ratio = calc_fairness(emulated_counters, metrics['fair_games_per_day'])
    return metrics['fairness_target'] - fairness_ratio

def increment_count_for_day(counters, day_id, increment):
    cindexerGet = lambda x: dict((p['day_id'],i) for i,p in enumerate(counters)).get(x)
    element = counters[cindexerGet(day_id)]
    element['count'] += increment


def find_swap_candidates(team_config, pref_unmet_sched, divteam_metrics):
    candidates = [{'div_id': x['div_id'], 'swap_sched': z} for x in divteam_metrics for y in x['team_data']
                  for z in y['schedule']
                  if not (team_config['tm_id'] in [z['home_id'], z['away_id']] and x['div_id'] == team_config['div_id'])
                  and z['round_id'] == pref_unmet_sched['round_id'] and z['game_date'].weekday() in team_config['prefdays']]
    return candidates

def calculate_initial_divteam_metrics(prefdays_list, pindexerGet, divinfo_list, dindexerGet,
                                      sched_tuple, fieldinfo_tuple):
    div_data_list = list()
    for divinfo in divinfo_list:
        team_totalgames = divinfo['totalgamedays']
        div_id = divinfo['div_id']
        fielddays = get_fielddays_per_week(divinfo['divfield_list'], fieldinfo_tuple)
        fair_games_per_day = float(team_totalgames) / len(fielddays)
        div_data = {'div_id': div_id, 'team_totalgames': team_totalgames, 'fair_games_per_day': fair_games_per_day}
        team_data_list = list()
        for team_id in range(1, divinfo['totalteams'] + 1):
            team_schedule = get_team_schedule(sched_tuple, div_id, team_id)
            pref_team_index = pindexerGet((div_id, team_id))
            counters = get_team_schedule_day_counts(team_schedule, fielddays)
            cindexerGet = lambda x: dict((p['day_id'],i) for i,p in enumerate(counters)).get(x)
            if pref_team_index is None:
                team_data = calc_initial_fairness_ratio(counters, fair_games_per_day)
                team_data.update({'team_id': team_id, 'counters': counters,
                                  'schedule': team_schedule, 'div_id': div_id,
                                  'ratio_type': 'fairness', 'totalgames': float(team_totalgames)})
            else:
                preference = prefdays_list[pref_team_index]
                team_data = calc_initial_pref_ratio(team_schedule, preference, fielddays, team_totalgames)
                team_data.update({'ratio_type': 'preference', 'schedule': team_schedule, 'div_id': div_id,
                                  'team_id': team_id, 'counters': counters, 'preference': preference,
                                  'totalgames': float(team_totalgames)})
            team_data_list.append(team_data)
        div_data['team_data'] = team_data_list
        div_data_list.append(div_data)
    return div_data_list

def get_team_schedule_day_counts(team_schedule, fielddays):
    sum_for_fieldday = lambda x: sum(1 for sched in team_schedule if sched['game_date'].weekday() == x)
    counters = [{'day_id': x, 'count': sum_for_fieldday(x)} for x in fielddays]
    return counters

def get_team_schedule(sched_tuple, div_id, team_id):
    div_sched = sched_tuple.dict_list[sched_tuple.indexerGet(div_id)]['sched_list']
    team_sched = [x for x in div_sched if x['home_id'] == team_id or x['away_id'] == team_id]
    return team_sched

def get_fielddays_per_week(fields, finfo_tuple):
    get_days = lambda x, y: x + finfo_tuple.dict_list[finfo_tuple.indexerGet(y)]['dayweek_list']
    combined_days = list(set(reduce(get_days, fields, [])))
    return combined_days

def calc_initial_pref_ratio(team_sched, preference, fielddays, team_totalgames):
    prefdays = preference['prefdays']
    satisfied_count = sum(1 for x in team_sched if x['game_date'].weekday() in prefdays)
    # ratio = float(team_totalgames - satisfied_count) / float(team_totalgames)
    default_ratio = float(len(prefdays)) / float(len(fielddays))
    target = 1.0 - (1.0 - default_ratio) / 2.0
    ratio = float(satisfied_count) / float(team_totalgames)
    return {'preference_ratio': ratio, 'preference_target': target, 'preference_satisfied_count': satisfied_count,
            'preference_cost': target - ratio, 'priority': preference['priority'] }

def calc_initial_fairness_ratio(counters, fair_games_per_day):
    fairness_ratio = calc_fairness(counters, fair_games_per_day)
    target = 0.9
    return {'fairness_ratio': fairness_ratio, 'fairness_target': target, 'fairness_cost': target - fairness_ratio,
            'fair_games_per_day': fair_games_per_day, 'priority':4}

def calc_fairness(counters, fair_games_per_day):
    fairness_square_sum = lambda x, y: x + ((y['count'] - fair_games_per_day)/fair_games_per_day)**2
    return 1.0 - sqrt(reduce(fairness_square_sum, counters, 0.0))

def get_team_totalgames(div_id, divinfo_list, dindexerGet):
    return divinfo_list[dindexerGet(div_id)]['totalgamedays']
