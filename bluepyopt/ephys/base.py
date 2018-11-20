'''Base class for ephys classes'''


class BaseEPhys(object):
    '''Base class for ephys classes'''

    def __init__(self, name='', comment=''):
        self.name = name
        self.comment = comment

    def __str__(self):
        return '%s: %s (%s)' % (self.__class__.__name__,
                                self.name, self.comment)
