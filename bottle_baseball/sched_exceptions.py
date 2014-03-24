''' Copyright YukonTR 2013 '''
# ref http://docs.python.org/2/tutorial/errors.html
# http://www.ibiblio.org/g2swap/byteofpython/read/raising-exceptions.html
class FieldAvailabilityError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, div_id):
        Exception.__init__(self)
        self.div_id = div_id
    def __str__(self):
        return repr(self.div_id)

class TimeSlotAvailabilityError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, field_id, round_id):
        Exception.__init__(self)
        self.field_id = field_id
        self.round_id = round_id
    def __str__(self):
        return "field "+str(self.field_id)+" gameday "+str(self.round_id)+" has no more slots"

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
    def __init__(self, msg, div_list):
        Exception.__init__(self)
        self.div_list = div_list
        self.msg = msg
    def __str__(self):
        return repr(self.msg) + "div_list="+reprr(self.msg)

class CodeLogicError(Exception):
    ''' Generic Exception if there is a logic error in code '''
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class SchedulerConfigurationError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
