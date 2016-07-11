import pytest
import datetime as dt
from pprint import pprint

@pytest.fixture(scope="module")
def team_config():
    return {'priority': 1, 'prefdays': [0], 'dt_id': u'dv3tm1', 'tm_id': 1, 'div_id': 3}

@pytest.fixture(scope="module")
def pref_unmet_sched():
    return {'home_id': 1, 'away_id': 3, 'round_id': 2, 'game_date': dt.datetime(2016, 6, 8, 0, 0),
            'fieldday_id': 3, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2}

@pytest.fixture(scope="module")
def divteam_metrics():
    metrics = [{'team_totalgames': 12, 'fair_games_per_day': 4.0, 'div_id': 3,
                'team_data': [{'ratio': 0.0, 'target': 0.6666666666666666,
                               'schedule': [{'home_id': 1, 'away_id': 3, 'round_id': 2,
                                             'game_date': dt.datetime(2016, 6, 8, 0, 0), 'fieldday_id': 3,
                                             'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                            {'home_id': 1, 'away_id': 5, 'round_id': 3, 'game_date': dt.datetime(2016, 6, 15, 0, 0),
                                             'fieldday_id': 6, 'start_time': dt.datetime(2016, 6, 25, 18, 0), 'field_id': 1, 'slot_index': 0},
                                            {'home_id': 1, 'away_id': 7, 'round_id': 4, 'game_date': dt.datetime(2016, 6, 22, 0, 0),
                                             'fieldday_id': 9, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                            {'home_id': 2, 'away_id': 1, 'round_id': 5, 'game_date': dt.datetime(2016, 6, 29, 0, 0),
                                             'fieldday_id': 12, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                            {'home_id': 5, 'away_id': 7, 'round_id': 13, 'game_date': dt.datetime(2016, 8, 3, 0, 0),
                                             'fieldday_id': 27, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2}],
                                'priority': 4, 'team_id': 1, 'div_id': 3, 'ratio_type': 'fairness',
                                'counters': [{'day_id': 0, 'count': 1}, {'day_id': 1, 'count': 5}, {'day_id': 2, 'count': 6}]},
                               {'ratio': 0.0, 'target': 0.6666666666666666,
                                'schedule': [{'home_id': 2, 'away_id': 3, 'round_id': 2,
                                              'game_date': dt.datetime(2016, 6, 6, 0, 0), 'fieldday_id': 3,
                                              'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                             {'home_id': 3, 'away_id': 5, 'round_id': 3, 'game_date': dt.datetime(2016, 6, 15, 0, 0),
                                              'fieldday_id': 6, 'start_time': dt.datetime(2016, 6, 25, 18, 0), 'field_id': 1, 'slot_index': 0},
                                             {'home_id': 3, 'away_id': 7, 'round_id': 4, 'game_date': dt.datetime(2016, 6, 22, 0, 0),
                                              'fieldday_id': 9, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                             {'home_id': 2, 'away_id': 3, 'round_id': 5, 'game_date': dt.datetime(2016, 6, 29, 0, 0),
                                              'fieldday_id': 12, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2},
                                             {'home_id': 3, 'away_id': 7, 'round_id': 13, 'game_date': dt.datetime(2016, 8, 3, 0, 0),
                                              'fieldday_id': 27, 'start_time': dt.datetime(2016, 6, 25, 20, 0), 'field_id': 1, 'slot_index': 2}],
                                 'priority': 4, 'team_id': 3, 'div_id': 3, 'ratio_type': 'fairness',
                                 'counters': [{'day_id': 0, 'count': 1}, {'day_id': 1, 'count': 5}, {'day_id': 2, 'count': 6}]}]
                }]
    return metrics

def test_find_opponent_metrics(team_config, pref_unmet_sched, divteam_metrics):
    from algorithm.teampreference import find_opponent_metrics
    metrics = find_opponent_metrics(team_config, pref_unmet_sched, divteam_metrics)
    assert 'div_id' in metrics.keys()
    assert 'team_id' in metrics.keys()
    assert team_config['div_id'] == metrics['div_id']
    assert team_config['tm_id'] != metrics['team_id']

def test_find_swap_candidates(team_config, pref_unmet_sched, divteam_metrics):
    from algorithm.teampreference import find_swap_candidates
    candidates = find_swap_candidates(team_config, pref_unmet_sched, divteam_metrics)
    pprint(candidates)
    assert len(candidates) == 1
    assert candidates[0]['swap_sched']['round_id'] == pref_unmet_sched['round_id']
    assert candidates[0]['swap_sched']['game_date'].weekday() in team_config['prefdays']
