"""Contains BluePyOpt specific exceptions."""


class MechAttributeError(AttributeError):
    """Raise when a mechanism does not contain the required param."""


class ParamMechMappingError(LookupError):
    """Raise when mapping of param to mechanism is ambiguous."""


class CreateAccException(Exception):
    """General exception raised while creating acc."""
