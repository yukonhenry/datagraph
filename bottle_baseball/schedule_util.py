'''Copyright YukonTR 2013 '''
from itertools import cycle, islice
import networkx as nx
from networkx import connected_components
from networkx.algorithms import bipartite
from collections import Iterable, namedtuple
from operator import itemgetter
from dateutil import parser
from datetime import timedelta
from bisect import bisect_right
import logging
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

''' create bipartite graph - one column is division, other column is fields
used to define relationship between division and fields
ref http://networkx.github.io/documentation/latest/reference/algorithms.bipartite.html'''
def getDivFieldEdgeWeight_list(divinfo_tuple, fieldinfo_list):
    divinfo_list = divinfo_tuple.dict_list
    divinfo_indexerGet = divinfo_tuple.indexerGet
    df_biparG = nx.Graph()
    df_biparG.add_nodes_from([x['div_id'] for x in divinfo_list], bipartite=0)
    # even through we are using a bipartite graph structure, node names between
    # the column nodes need to be distinct, or else edge (1,2) and (2,1) are not distinguished.
    # instead use edge (1, f2), (2, f1) - use 'f' prefix for field nodes
    df_biparG.add_edges_from([(x['div_id'],'f'+str(y)) for x in divinfo_list for y in x['fields']])
    div_nodes, field_nodes = bipartite.sets(df_biparG)
    deg_fnodes = {f:df_biparG.degree(f) for f in field_nodes}
    # effective edge sum lists for each division, the sum of the weights of the connected fields;
    # the weights of the associated fields, which are represented as field nodes,
    # are in turn determined by it's degree.  The inverse of the degree for the connected division is
    # taken, which becomes the weight of the particular field associated with the division.  The weights
    # of each field are summed for each division.  The weights also represent the 'total fairness share'
    # of fields associated with a division.
    # Bipartite graph representations, with divisions as one set of nodes, and fields as the other set
    # are used.  Thus a neighbor of a division is always a field.
    edgesum_list = [{'div_id':d,
        'edgesum': sum([1.0/deg_fnodes[f] for f in df_biparG.neighbors(d)])} for d in div_nodes]
    sorted_edgesum_list = sorted(edgesum_list, key=itemgetter('div_id'))
    logging.debug("div fields bipartite graph %s %s effective edge sum for each node %s", df_biparG.nodes(), df_biparG.edges(), sorted_edgesum_list)

    # depending on the number of teams in each division, the 'fairness share' for each division is adjusted;
    # i.e. a division with more teams is expected to contribute a larger amount to field sharing obligations,
    # such as the number of expected early/late start times for a particular division.  (If one div has 20 teams
    # and the other connected div has only 10 teams, the 20-team division should have a larger share of filling
    # early and late start time games.
    # ratio is represented as factor that is multiplied against the 'expected' fair share, which is the 1-inverse
    # of the number of divisions in the connected group - (dividing by the 1-inverse is equiv to multiple by the
    # number of teams - len(connected_list) as shown below)
    divratio_list = [{'div_id':x,
        'ratio': len(connected_list)*float(divinfo_list[divinfo_indexerGet(x)]['totalteams'])/sum(divinfo_list[divinfo_indexerGet(y)]['totalteams'] for y in connected_list)} for connected_list in getConnectedDivisionGroup(fieldinfo_list) for x in connected_list]
    sorted_divratio_list = sorted(divratio_list, key=itemgetter('div_id'))
    # multiply sorted edgesum list elements w. sorted divratio list elements
    # because of the sort all dictionary elements in the list should be sorted according to div_id and obviating
    # need to create an indexerGet function
    # x['div_id'] could have been y['div_id'] in the list comprehension below
    prod_list = [{'div_id': x['div_id'], 'prodratio': x['edgesum']*y['ratio']}
                             for (x,y) in zip(sorted_edgesum_list, sorted_divratio_list)]
    logging.debug("getDivFieldEdgeWeight: sorted_edge=%s, sorted_ratio=%s, prod=%s",
                                sorted_edgesum_list, sorted_divratio_list, prod_list)
    # define indexer function object
    prod_indexerGet = lambda x: dict((p['div_id'],i) for i,p in enumerate(prod_list)).get(x)
    return _List_Indexer(prod_list, prod_indexerGet)

def convertJStoPY_daylist(jsday_list):
    '''Convert list of days from JS format (Sun/0 to Sat/6) to Python day format
    (Mon/0 to Sun/6)'''
    pyday_list = [(j-1)%7 for j in jsday_list]
    return pyday_list

def convertPYtoJS_daylist(pyday_list):
    '''Inverse of convertJStoPY_daylist().  Convert list of days from PY to JS format'''
    jsday_list = [(p+1)%7 for p in pyday_list]
    return jsday_list

def find_le(a, x):
    '''Find rightmost value less than or equal to x
    ref https://docs.python.org/2/library/bisect.html'''
    i = bisect_right(a, x)
    if i:
        return_index = i-1
        return (return_index, a[return_index])
    raise ValueError

def getcalendarmap_list(dayweek_list, start_date_str, totalfielddays):
    '''Get list that maps fieldday_id to calendar date; field_id is index+1 of list
    Returning a list is more convenient than returing a dictionary/obj
    as a list is more convenient for use in an intersection function.
    Start Date is a datetime object as Date objects cannot be serialized
    to be written in as a doc for mongodb '''
    #start_date = parser.parse(start_date_str).date()
    start_date = parser.parse(start_date_str)
    start_day = start_date.weekday()
    fielddaymapdate_list = []
    dayweek_len = len(dayweek_list)
    #find first actual start day by finding the first day from the dayweek_list
    # that is past the start_date which is selected from the UI calendar.
    try:
        firststart_index, firststart_day = find_le(dayweek_list, start_day)
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
        mapdate_list.append(next_date)
        #get the next index into the gap list
        #if index is length of list, then roll over to 0
        next_index = (next_index+1) % dayweek_len
        next_date += gap_list[next_index];
    return mapdate_list
