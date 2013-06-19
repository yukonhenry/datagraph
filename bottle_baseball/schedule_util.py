from itertools import cycle, islice
# ref http://docs.python.org/2/library/itertools.html
# ref http://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))
