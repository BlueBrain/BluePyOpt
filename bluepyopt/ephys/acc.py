'''Dependencies of Arbor simulator backend'''

try:
    import arbor
except ImportError as e:
    class arbor:
        def __getattribute__(self, _):
            raise ImportError("Exporting cell models to ACC/JSON, loading"
                              " them or optimizing them with the Arbor"
                              " simulator requires missing dependency arbor."
                              " To install BluePyOpt with arbor,"
                              " run 'pip install bluepyopt[arbor]'.")


class ArbLabel:
    """Arbor label"""

    def __init__(self, type, name, s_expr):
        if type not in ['locset', 'region', 'iexpr']:
            raise ValueError('Invalid Arbor label type %s' % type)
        self._type = type
        self._name = name
        self._s_expr = s_expr

    @property
    def defn(self):
        """Label definition for label-dict"""
        return '(%s-def "%s" %s)' % (self._type, self._name, self._s_expr)

    @property
    def ref(self):
        """Reference to label defined in label-dict"""
        return '(%s "%s")' % (self._type, self._name)

    @property
    def name(self):
        """Name of the label"""
        return self._name

    @property
    def loc(self):
        """S-expression defining the location of the label"""
        return self._s_expr

    def __eq__(self, other):
        if other is None:
            return False
        elif not isinstance(other, ArbLabel):
            raise TypeError('%s is not an ArbLabel' % str(other))
        else:
            return self._s_expr == other._s_expr

    def __hash__(self):
        return hash(self._s_expr)

    def __repr__(self):
        return self.defn
