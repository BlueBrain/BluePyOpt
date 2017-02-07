'''Mixin class to make dictionaries'''
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# Disabling lines below, generate error when loading ephys.examples
# from future import standard_library
# standard_library.install_aliases()


SENTINAL = 'class'


class DictMixin(object):

    '''Mixin class to create dictionaries of selected elements'''
    SERIALIZED_FIELDS = ()

    @staticmethod
    def _serializer(value):
        """_serializer"""
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        elif isinstance(value, (list, tuple)) and \
                value and hasattr(value[0], 'to_dict'):
            return [v.to_dict() for v in value]
        elif(isinstance(value, dict) and value and
             hasattr(next(iter(list(value.values()))), 'to_dict')):
            return {k: v.to_dict() for k, v in list(value.items())}
        return value

    @staticmethod
    def _deserializer(value):
        """_deserializer"""
        if(isinstance(value, list) and value and
           isinstance(value[0], dict) and SENTINAL in value[0]):
            return [instantiator(v) for v in value]
        elif isinstance(value, dict) and value:
            if SENTINAL in value:
                return instantiator(value)
            model_value = next(iter(list(value.values())))
            if isinstance(model_value, dict) and SENTINAL in model_value:
                return {k: instantiator(v) for k, v in list(value.items())}
        return value

    def to_dict(self):
        '''create dictionary'''
        ret = {}
        for field in self.SERIALIZED_FIELDS:
            ret[field] = DictMixin._serializer(getattr(self, field))
        ret['class'] = repr(self.__class__)
        return ret

    @classmethod
    def from_dict(cls, fields):
        '''create class from serialized values'''
        klass = fields[SENTINAL]
        assert klass == repr(cls), 'Class names much match %s != %s' % (
            klass, repr(cls))
        del fields['class']
        for name in list(fields.keys()):
            fields[name] = DictMixin._deserializer(fields[name])
        return cls(**fields)


def instantiator(fields):
    """instantiator"""
    klass = fields[SENTINAL]
    for subclass in DictMixin.__subclasses__():
        if repr(subclass) == klass:
            return subclass.from_dict(fields)
    raise Exception('Could not find class "%s" to instantiate' % klass)
