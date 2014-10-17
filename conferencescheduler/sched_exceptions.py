# ref http://docs.python.org/2/tutorial/errors.html
# http://www.ibiblio.org/g2swap/byteofpython/read/raising-exceptions.html

class CodeLogicError(Exception):
    ''' Generic Exception if there is a logic error in code '''
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
