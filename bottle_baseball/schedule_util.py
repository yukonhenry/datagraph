'''Copyright YukonTR 2013 '''
from itertools import cycle, islice
import networkx as nx
from networkx import connected_components
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
    for j in xrange(nth):
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
# this should be simplier than the method below whith utilize the division info list
# note there is an identical function (w different name) in leaguedivprocess - eventuall
# migrate to using this function.
def getConnectedDivisionGroup(fieldinfo_list):
    G = nx.Graph()
    for field in fieldinfo_list:
        prev_node = None
        for div_id in field['primary']:
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
