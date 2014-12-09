'''Copyright YukonTR 2013 '''
from itertools import cycle, islice
import networkx as nx
from networkx import connected_components
from networkx.algorithms import bipartite
from collections import Iterable, namedtuple
from operator import itemgetter
from dateutil import parser
from datetime import timedelta
from bisect import bisect_right, bisect_left
import logging
import os, errno
_List_Indexer = namedtuple('List_Indexer', 'dict_list indexerGet')

def roundrobin(iterable_list):
    '''ref http://docs.python.org/2/library/itertools.html
    # ref http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
    # modified to assume argument is list of lists (instead of comma separated lists)
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis '''
    pending = len(iterable_list)
    nexts = cycle(iter(it).next for it in iterable_list)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


def all_same(items):
    # ref http://stackoverflow.com/questions/3787908/python-determine-if-all-items-of-a-list-are-the-same-item
    return all(x == items[0] for x in items)

def all_value(items, value):
    return all(x == value for x in items)

def all_isless(items, value):
    return all(x < value for x in items)

def any_ismore(items, value):
    return any(x > value for x in items)

def any_isless(items, value):
    return any(x < value for x in items)


def enum(**enums):
    ''' ref for enums http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python'''
    return type('Enum', (), enums)

def shift_list(l, shift, empty=0):
    '''http://stackoverflow.com/questions/9209999/python-shift-elements-in-a-list-with-constant-length
    first param l is the list, shift is the number of positions (positive shift is to right, negative
    to left), empty is the fill-in value'''
    src_index = max(-shift, 0)
    dst_index = max(shift, 0)
    length = max(len(l) - abs(shift), 0)
    new_l = [empty] * len(l)
    new_l[dst_index:dst_index + length] = l[src_index:src_index + length]
    return new_l

def nth_listitem(l, val, nth):
    '''http://stackoverflow.com/questions/8337069/find-the-index-of-the-nth-item-in-a-list
    nth vallue is 1-indexed as expected, returned value is 0-indexed position in array
    nth = 0 returns -1
    if nth value does not exist, return -1 also (based on ValueError exception within function)'''
    i = -1
    for j in range(nth):
        try:
            i = l.index(val, i + 1)
        except ValueError:
            return -1
    return i


# from
# http://code.google.com/p/uthcode/source/browse/trunk/python/bipartite.py?r=662
# http://www.downscripts.com/hopcroft-karp-bipartite-matching_python-script.html
# Hopcroft-Karp bipartite max-cardinality matching and max independent set
# David Eppstein, UC Irvine, 27 Apr 2002

def bipartiteMatch(graph):
	'''Find maximum cardinality matching of a bipartite graph (U,V,E).
	The input format is a dictionary mapping members of U to a list
	of their neighbors in V.  The output is a triple (M,A,B) where M is a
	dictionary mapping members of V to their matches in U, A is the part
	of the maximum independent set in U, and B is the part of the MIS in V.
	The same object may occur in both U and V, and is treated as two
	distinct vertices if this happens.'''

	# initialize greedy matching (redundant, but faster than full search)
	matching = {}
	for u in graph:
		for v in graph[u]:
			if v not in matching:
				matching[v] = u
				break

	while 1:
		# structure residual graph into layers
		# pred[u] gives the neighbor in the previous layer for u in U
		# preds[v] gives a list of neighbors in the previous layer for v in V
		# unmatched gives a list of unmatched vertices in final layer of V,
		# and is also used as a flag value for pred[u] when u is in the first layer
		preds = {}
		unmatched = []
		pred = dict([(u,unmatched) for u in graph])
		for v in matching:
			del pred[matching[v]]
		layer = list(pred)

		# repeatedly extend layering structure by another pair of layers
		while layer and not unmatched:
			newLayer = {}
			for u in layer:
				for v in graph[u]:
					if v not in preds:
						newLayer.setdefault(v,[]).append(u)
			layer = []
			for v in newLayer:
				preds[v] = newLayer[v]
				if v in matching:
					layer.append(matching[v])
					pred[matching[v]] = v
				else:
					unmatched.append(v)

		# did we finish layering without finding any alternating paths?
		if not unmatched:
			unlayered = {}
			for u in graph:
				for v in graph[u]:
					if v not in preds:
						unlayered[v] = None
			return (matching,list(pred),list(unlayered))

		# recursively search backward through layers to find alternating paths
		# recursion returns true if found path, false otherwise
		def recurse(v):
			if v in preds:
				L = preds[v]
				del preds[v]
				for u in L:
					if u in pred:
						pu = pred[u]
						del pred[u]
						if pu is unmatched or recurse(pu):
							matching[v] = u
							return 1
			return 0

		for v in unmatched: recurse(v)

#find inter-related divisions through the field_info list
# this should be simplier than the method below which utilize the division info list
# note there is an identical function (w different name) in leaguedivprocess - eventuall
# migrate to using this function.
def getConnectedDivisionGroup(fieldinfo_list, key='primaryuse_list'):
    G = nx.Graph()
    for field in fieldinfo_list:
        prev_node = None
        for div_id in field[key]:
            if not G.has_node(div_id):
                G.add_node(div_id)
            if prev_node is not None and not G.has_edge(prev_node, div_id):
                G.add_edge(prev_node, div_id)
            prev_node = div_id
    connected_div_components = connected_components(G)
    #serialize field-connected divisions as graph and save it
    #(instead of saving list of connected components); used by leaguediv_process to
    #determine schedule allocation of connected divisions
    #connected_graph = json_graph.node_link_data(G)
    return connected_div_components

# flatten arbitrarily nested lists
# http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def convertJStoPY_daylist(jsday_list):
    '''Convert list of days from JS format (Sun/0 to Sat/6) to Python day format
    (Mon/0 to Sun/6); sort list'''
    pyday_list = [(j-1)%7 for j in jsday_list]
    pyday_list.sort()
    return pyday_list

def convertPYtoJS_daylist(pyday_list):
    '''Inverse of convertJStoPY_daylist().  Convert list of days from PY to JS format; sort list'''
    jsday_list = [(p+1)%7 for p in pyday_list]
    jsday_list.sort()
    return jsday_list

def find_le(a, x):
    '''Find rightmost value less than or equal to x
    ref https://docs.python.org/2/library/bisect.html'''
    i = bisect_right(a, x)
    if i:
        return_index = i-1
        return (return_index, a[return_index])
    raise ValueError

def find_ge(a,x):
    '''Find leftmost value greater than or equal to x
    ref https://docs.python.org/2/library/bisect.html'''
    i = bisect_left(a, x)
    if i != len(a):
        return_index = i
        return (return_index, a[return_index])
    raise ValueError

def mkdir_p(path):
    ''' http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    '''
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def getcalendarmap_list(dayweek_list, start_date_str, totalfielddays):
    '''Get list that maps fieldday_id to calendar date;
    Start Date is a datetime object as Date objects cannot be serialized
    to be written in as a doc for mongodb '''
    #start_date and next_date are dt objects (instead of date obj) so that we can
    # to addition operations with timedelta objects
    start_date = parser.parse(start_date_str)
    start_day = start_date.weekday()
    fielddaymapdate_list = []
    dayweek_len = len(dayweek_list)
    #find first actual start day by finding the first day from the dayweek_list
    # that is past the start_date which is selected from the UI calendar.
    try:
        firststart_index, firststart_day = find_ge(dayweek_list, start_day)
    except ValueError:
        # case where the firststart_day is the first day in the list
        firststart_index, firststart_day = (0, dayweek_list[0])
    # calculate how many days the firststart_day is past the start_day
    # take care of case where firststart_day weekday id is lower value than the
    # weekday identifier for the start_day
    diff = firststart_day - start_day
    firststart_diff = diff if diff >= 0 else diff+7
    first_date = start_date + timedelta(firststart_diff)
    #create list that maps fieldday to actual calendar date, with position in
    # list corresponding to fieldday_id
    # First create list whose elements are num days gap with the previous dayweek element
    #get the last element, but offset it by 7 (length of week); do this as the gap
    #calculation for the first element should be
    #first_gap  = first_elem +7 - last_elem
    #           = first_elem - (last_elem - 7)
    gap_list = [];
    prev_elem = dayweek_list[dayweek_len-1]-7;
    for dayweek in dayweek_list:
        gap_list.append(timedelta(dayweek-prev_elem))
        prev_elem = dayweek
    next_index, next_date = (firststart_index, first_date)
    #generate list that maps fieldday_id (represented as position in list) to
    #calendar date string
    mapdate_list = []
    for fieldday_id in range(1, totalfielddays+1):
        mapdate_list.append({'fieldday_id':fieldday_id, 'date':next_date})
        #get the next index into the gap list
        #if index is length of list, then roll over to 0
        next_index = (next_index+1) % dayweek_len
        next_date += gap_list[next_index];
    return mapdate_list
