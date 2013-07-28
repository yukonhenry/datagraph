from itertools import cycle, islice

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

def enum(**enums):
    ''' ref for enums http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python'''
    return type('Enum', (), enums)

def shift_list(l, shift, empty=0):
    '''http://stackoverflow.com/questions/9209999/python-shift-elements-in-a-list-with-constant-length '''
    src_index = max(-shift, 0)
    dst_index = max(shift, 0)
    length = max(len(l) - abs(shift), 0)
    new_l = [empty] * len(l)
    new_l[dst_index:dst_index + length] = l[src_index:src_index + length]
    return new_l
