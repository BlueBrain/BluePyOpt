"""Main Graupner-Brunel STDP example script"""

import numpy

import bluepyopt as bpop
import stdputil


def gbParam(params):
    """Create the parameter set for Graupner-Brunel model from an *individual*.

    :param individual: iterable
    :rtype : dict
    """
    gbparam = dict(
        theta_d=1.0,
        theta_p=1.3,
        rho_star=0.5,
        beta=0.75)  # Fixed params

    for param_name, param_value in params:
        gbparam[param_name] = param_value

    return gbparam


class GraupnerBrunelEvaluator(bpop.evaluators.Evaluator):

    """Graupner-Brunel Evaluator"""

    def __init__(self):
        """Constructor"""

        super(GraupnerBrunelEvaluator, self).__init__()
        # Graupner-Brunel model parameters and boundaries,
        # from (Graupner and Brunel, 2012)
        self.graup_params = [('tau_ca', 1e-3, 100e-3),
                             ('C_pre', 0.1, 20.0),
                             ('C_post', 0.1, 50.0),
                             ('gamma_d', 5.0, 5000.0),
                             ('gamma_p', 5.0, 2500.0),
                             ('sigma', 0.35, 70.7),
                             ('tau', 2.5, 2500.0),
                             ('D', 0.0, 50e-3),
                             ('b', 1.0, 100.0)]

        self.params = [bpop.parameters.Parameter
                       (param_name, bounds=(min_bound, max_bound))
                       for param_name, min_bound, max_bound in self.
                       graup_params]

        self.param_names = [param.name for param in self.params]

        self.protocols, self.sg, self.stdev, self.stderr = \
            stdputil.load_neviansakmann()

        self.objectives = [bpop.objectives.Objective(protocol.prot_id)
                           for protocol in self.protocols]

    def get_param_dict(self, param_values):
        """Build dictionary of parameters for the Graupner-Brunel model from an
        ordered list of values (i.e. an individual).

        :param param_values: iterable
            Parameters list
        """
        return gbParam(zip(self.param_names, param_values))

    def compute_synaptic_gain_with_lists(self, param_values):
        """Compute synaptic gain for all protocols.

        :param param_values: iterable
            Parameters list
        """
        param_dict = self.get_param_dict(param_values)

        syn_gain = [stdputil.protocol_outcome(protocol, param_dict)
                    for protocol in self.protocols]

        return syn_gain

    def evaluate_with_lists(self, param_values):
        """Evaluate individual

        :param param_values: iterable
            Parameters list
        """
        param_dict = self.get_param_dict(param_values)

        err = []
        for protocol, sg, stderr in \
                zip(self.protocols, self.sg, self.stderr):
            res = stdputil.protocol_outcome(protocol, param_dict)

            err.append(numpy.abs(sg - res) / stderr)

        return err
