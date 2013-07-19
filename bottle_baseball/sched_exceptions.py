# ref http://docs.python.org/2/tutorial/errors.html
# http://www.ibiblio.org/g2swap/byteofpython/read/raising-exceptions.html
class FieldAvailabilityError(Exception):
    '''A user-defined exception class.'''
    def __init__(self, div_id):
        Exception.__init__(self)
        self.div_id = div_id
