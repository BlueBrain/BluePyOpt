'''Mixin class to make dictionaries'''


SENTINAL = 'class'

class DictMixin(object):
    '''Mixin class to create dictionaries of selected elements'''
    SERIALIZED_FIELDS = ()

    @staticmethod
    def _serializer(value):
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        elif isinstance(value, (list, tuple)) and value and hasattr(value[0], 'to_dict'):
            return [v.to_dict() for v in value]
        elif(isinstance(value, dict) and value and
             hasattr(iter(value.values()).next(), 'to_dict')):
            return {k: v.to_dict() for k, v in value.iteritems()}
        return value

    @staticmethod
    def _deserializer(value):
        if(isinstance(value, list) and value and
           isinstance(value[0], dict) and SENTINAL in value[0]):
            return [instantiator(v) for v in value]
        elif isinstance(value, dict) and value:
            if SENTINAL in value:
                return instantiator(value)
            model_value = iter(value.values()).next()
            if isinstance(model_value, dict) and SENTINAL in model_value:
                return {k: instantiator(v) for k, v in value.iteritems()}
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
        assert klass == repr(cls), 'Class names much match %s != %s' % (klass, repr(cls))
        del fields['class']
        for name in fields.keys():
            fields[name] = DictMixin._deserializer(fields[name])
        return cls(**fields)


def instantiator(fields):
    klass = fields[SENTINAL]
    for subclass in DictMixin.__subclasses__():
        if repr(subclass) == klass:
            return subclass.from_dict(fields)
    raise Exception('Could not find class "%s" to instantiate' % klass)
