"""Contains NEURON to Arbor mapping functionalities."""

from collections import namedtuple
import logging

from bluepyopt.ephys.create_hoc import (
    RangeExpr, PointExpr, Location, format_float)
from bluepyopt.ephys.morphologies import ArbFileMorphology

from bluepyopt.exceptions import (
    MechAttributeError,
    ParamMechMappingError,
)


logger = logging.getLogger(__name__)


# Inhomogeneous expression for scaled parameter in Arbor
RangeIExpr = namedtuple('RangeIExpr', 'name, value, scale')


class ArbVar:
    """Arbor variable with conversion function"""
    def __init__(self, name, conv=None):
        self.name = name
        self.conv = conv

    def __repr__(self):
        return 'ArbVar(%s, %s)' % (self.name, self.conv)


class Nrn2ArbAdapter:
    """Adapter from NEURON to Arbor."""

    mapping = dict(
        v_init=ArbVar(name="membrane-potential"),
        celsius=ArbVar(
            name="temperature-kelvin", conv=lambda celsius: celsius + 273.15
        ),
        Ra=ArbVar(name="axial-resistivity"),
        cm=ArbVar(
            name="membrane-capacitance", conv=lambda cm: cm / 100.0
        ),  # NEURON: uF/cm^2, Arbor: F/m^2
        **{
            species
            + loc[0]: ArbVar(
                name='ion-%sternal-concentration "%s"' % (loc, species)
            )
            for species in ["na", "k", "ca"]
            for loc in ["in", "ex"]
        },
        **{
            "e" + species: ArbVar(name='ion-reversal-potential "%s"' % species)
            for species in ["na", "k", "ca"]
        },
    )

    @classmethod
    def var_name(cls, name) -> str:
        return cls.mapping[name].name if name in cls.mapping else name

    @classmethod
    def var_value(cls, param):
        """Neuron to Arbor units conversion for parameter values

        Args:
            param (): A Neuron parameter with a value in Neuron units
        """
        if (
            param.name in cls.mapping
            and cls.mapping[param.name].conv is not None
        ):
            return format_float(
                cls.mapping[param.name].conv(float(param.value))
            )
        else:
            return param.value

    @classmethod
    def parameter(cls, param, name):
        """Convert a Neuron parameter to Arbor format (name and units)

        Args:
            param (): A Neuron parameter
        """

        if isinstance(param, Location):
            return Location(name=cls.var_name(name),
                            value=cls.var_value(param))
        elif isinstance(param, RangeExpr):
            return RangeExpr(
                location=param.location,
                name=cls.var_name(name),
                value=cls.var_value(param),
                value_scaler=param.value_scaler,
            )
        elif isinstance(param, PointExpr):
            return PointExpr(
                name=cls.var_name(name),
                point_loc=param.point_loc,
                value=cls.var_value(param),
            )
        else:
            raise TypeError("Invalid parameter expression type.")

    @staticmethod
    def mech_name(name):
        """Neuron to Arbor mechanism name conversion

        Args:
            name (): A Neuron mechanism name
        """
        if name in ['Exp2Syn', 'ExpSyn']:
            return name.lower()
        else:
            return name


def _arb_nmodl_translate_mech(mech_name, mech_params, arb_cats):
    """Translate NMODL mechanism to Arbor ACC format

    Args:
        mech_name (): NMODL mechanism name (suffix)
        mech_params (): Mechanism parameters in Arbor format
        arb_cats (): Mapping of catalogue names to mechanisms
        with theirmeta data

    Returns:
        Tuple of mechanism name with NMODL GLOBAL parameters integrated and
        catalogue prefix added as well as the remaining RANGE parameters
    """
    arb_mech = None
    arb_mech_name = Nrn2ArbAdapter.mech_name(mech_name)

    for cat in arb_cats:  # in order of precedence
        if arb_mech_name in arb_cats[cat]:
            arb_mech = arb_cats[cat][arb_mech_name]
            mech_name = cat + '::' + arb_mech_name
            break

    if arb_mech is None:  # not Arbor built-in mech, no qualifier added
        if mech_name is not None:
            logger.warn('create_acc: Could not find Arbor mech for %s (%s).'
                        % (mech_name, mech_params))
        return (mech_name, mech_params)
    else:
        if arb_mech.globals is None:  # only Arbor range params
            for param in mech_params:
                if param.name not in arb_mech.ranges:
                    raise MechAttributeError(
                        '%s not a GLOBAL or RANGE parameter of %s' %
                        (param.name, mech_name))
            return (mech_name, mech_params)
        else:
            for param in mech_params:
                if param.name not in arb_mech.globals and \
                        param.name not in arb_mech.ranges:
                    raise MechAttributeError(
                        '%s not a GLOBAL or RANGE parameter of %s' %
                        (param.name, mech_name))
            mech_name_suffix = []
            remaining_mech_params = []
            for mech_param in mech_params:
                if mech_param.name in arb_mech.globals:
                    mech_name_suffix.append(mech_param.name + '=' +
                                            mech_param.value)
                    if isinstance(mech_param, RangeIExpr):
                        remaining_mech_params.append(
                            RangeIExpr(name=mech_param.name,
                                       value=None,
                                       scale=mech_param.scale))
                else:
                    remaining_mech_params.append(mech_param)
            if len(mech_name_suffix) > 0:
                mech_name += '/' + ','.join(mech_name_suffix)
            return (mech_name, remaining_mech_params)


def arb_nmodl_translate_density(mechs, arb_cats):
    """Translate all density mechanisms in a specific region"""
    return dict([_arb_nmodl_translate_mech(mech, params, arb_cats)
                 for mech, params in mechs.items()])


def arb_nmodl_translate_points(mechs, arb_cats):
    """Translate all point mechanisms for a specific locset"""
    result = dict()

    for synapse_name, mech_desc in mechs.items():
        mech, params = _arb_nmodl_translate_mech(
            mech_desc['mech'], mech_desc['params'], arb_cats)
        result[synapse_name] = dict(mech=mech,
                                    params=params)

    return result


def _find_mech_and_convert_param_name(param, mechs):
    """Find a parameter's mechanism and convert name to Arbor format

    Args:
        param (): A parameter in Neuron format
        mechs (): List of co-located NMODL mechanisms

    Returns:
        A tuple of mechanism name (None for a non-mechanism parameter) and
        parameter in Arbor format
    """
    if not isinstance(param, PointExpr):
        mech_matches = [i for i, mech in enumerate(mechs)
                        if param.name.endswith("_" + mech)]
    else:
        param_pprocesses = [loc.pprocess_mech for loc in param.point_loc]
        mech_matches = [i for i, mech in enumerate(mechs)
                        if mech in param_pprocesses]

    if len(mech_matches) == 0:
        return None, Nrn2ArbAdapter.parameter(param, name=param.name)

    elif len(mech_matches) == 1:
        mech = mechs[mech_matches[0]]
        if not isinstance(param, PointExpr):
            name = param.name[:-(len(mech) + 1)]
        else:
            name = param.name
        return mech, Nrn2ArbAdapter.parameter(param, name=name)

    else:
        raise ParamMechMappingError(
            "Parameter name {} matches"
            + f" multiple mechanisms {[repr(mechs[i]) for i in mech_matches]}"
        )


def _arb_convert_params_and_group_by_mech(params, channels):
    """Turn list of Neuron parameters to Arbor format and group by mechanism

    Args:
        params (): List of parameters in Neuron format
        channels (): List of co-located NMODL mechanisms

    Returns:
        Mapping of Arbor mechanism name to list of parameters in Arbor format
    """
    mech_params = [_find_mech_and_convert_param_name(
                   param, channels) for param in params]
    mechs = {mech: [] for mech, _ in mech_params}
    for mech in channels:
        if mech not in mechs:
            mechs[mech] = []
    for mech, param in mech_params:
        mechs[mech].append(param)
    return mechs


def arb_convert_params_and_group_by_mech_global(params: dict):
    """Group global params by mechanism, convert them to Arbor format"""
    return _arb_convert_params_and_group_by_mech(
        [Location(name=name, value=value) for name, value in params.items()],
        []  # no default mechanisms
    )


def arb_convert_params_and_group_by_mech_local(params, channels):
    """Group local params by mechanism, convert them to Arbor format

    Args:
        params (): List of Arbor label/local parameters pairs in Neuron format
        channels (): Mapping of Arbor label to co-located NMODL mechanisms

    Returns:
        Mapping of Arbor label to mechanisms with their parameters in Arbor
        format (mechanism name is None for non-mechanism parameters) in the
        first component, global properties found in the second
    """
    local_mechs = dict()
    for loc, params in params:
        mechs = _arb_convert_params_and_group_by_mech(params, channels[loc])

        # move Arbor global properties to global_params
        global_properties = _get_global_arbor_properties(loc, mechs)
        local_properties = _get_local_arbor_properties(loc, mechs)
        if local_properties != []:
            mechs[None] = local_properties
        local_mechs[loc] = mechs
    return local_mechs, global_properties


def _arb_is_global_property(label, param):
    """Returns if a label-specific variable is a global property in Arbor

    Args:
        label (ArbLabel): An Arbor label describing the location
        param: A parameter in Arbor format (name and units)
    """
    return label == ArbFileMorphology.region_labels['all'] and (
        param.name in ['membrane-potential',
                       'temperature-kelvin',
                       'axial-resistivity',
                       'membrane-capacitance'] or
        param.name.split(' ')[0] in ['ion-internal-concentration',
                                     'ion-external-concentration',
                                     'ion-reversal-potential'])


def _get_global_arbor_properties(label, mechs):
    """Returns global properties from a label-specific dict of mechanisms

    Args:
        label: An Arbor label describing the location
        mechs: A mapping of mechanism name to list of parameters in

    Returns:
        A list of global properties
    """
    if None not in mechs:
        return []
    return [p for p in mechs[None] if _arb_is_global_property(label, p)]


def _get_local_arbor_properties(label, mechs):
    """Returns local properties from a label-specific dict of mechanisms

    Args:
        label: An Arbor label describing the location
        mechs: A mapping of mechanism name to list of parameters in

    Returns:
        A list of local properties
    """
    if None not in mechs:
        return []
    return [p for p in mechs[None] if not _arb_is_global_property(label, p)]
