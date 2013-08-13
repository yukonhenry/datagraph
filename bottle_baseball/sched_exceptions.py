# ref http://docs.python.org/2/tutorial/errors.html
# http://www.ibiblio.org/g2swap/byteofpython/read/raising-exceptions.html
class FieldAvailabilityError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, div_id):
        Exception.__init__(self)
        self.div_id = div_id

class TimeSlotAvailabilityError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, field_id):
        Exception.__init__(self)
        self.field_id = field_id

class TimeCompactionError(Exception):
    '''Raised if there is some problem compacting the time schedule
    (eliminating time gamps)'''
    def __init__(self, field_id, gameday_id):
        Exception.__init__(self)
        self.field_id = field_id
        self.gameday_id = gameday_id

class FieldConsistencyError(Exception):
    '''Raised if there is some unexpected inconsistency for allocated fields for a division'''
    def __init__(self, field_list1, field_list2):
        Exception.__init__(self)
        self.field_list1 = field_list1
        self.field_list2 = field_list2

class FieldTimeAvailabilityError(Exception):
    ''' Raised if there is a general lack of fields or time to service required number of games'''
    def __init__(self, div_list):
        Exception.__init__(self)
        self.div_list = div_list
