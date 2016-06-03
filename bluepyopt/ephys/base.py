'''Base class for ephys classes'''


class BaseEPhys(object):
    def __init__(self, name='', comment=''):
        """init"""
        self.name = name
        self.comment = comment

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.name, self.comment)
