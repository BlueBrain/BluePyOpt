"""Main Graupner STDP example script"""

import numpy

import bluepyopt as bpop
import stdputil


def graupnerParam(params):
    """Create the parameter set for the Graupner model from an *individual*.

    :param individual: iterable
    :rtype : dict
    """
    gparam = dict(
        theta_d=1.0,
        theta_p=1.3,
        rho_star=0.5,
        beta=0.75)  # Fixed params

    for param_name, param_value in params:
        gparam[param_name] = param_value

    return gparam


class GraupnerEvaluator(bpop.evaluators.Evaluator):

    """Graupner Evaluator"""

    def __init__(self):
        """Constructor"""

        super(GraupnerEvaluator, self).__init__()
        # Graupner model parameters and boundaries
        self.graup_params = [('tau_ca', 1e-3, 100e-3),
                             ('C_pre', 0.1, 5.0),
                             ('C_post', 0.1, 5.0),
                             ('gamma_d', 5.0, 5000.0),
                             ('gamma_p', 5.0, 2500.0),
                             ('sigma', 0.35, 70.7),
                             ('tau', 2.5, 2500.0),
                             ('D', 0.0, 50e-3),
                             ('b', 1.0, 10.0)]

        self.params = [bpop.parameters.Parameter
                       (param_name, bounds=(min_bound, max_bound))
                       for param_name, min_bound, max_bound in self.
                       graup_params]

        self.param_names = [param.name for param in self.params]

        self.protocols, self.sg, self.stdev, self.stderr = \
            stdputil.load_neviansakmann()

        self.objectives = [bpop.objectives.Objective(protocol.prot_id)
                           for protocol in self.protocols]

    def evaluate_with_lists(self, param_values):
        """Evaluate"""
        param_dict = graupnerParam(zip(self.param_names, param_values))

        err = []
        for protocol, sg, stderr in \
                zip(self.protocols, self.sg, self.stderr):
            res = stdputil.protocol_outcome(protocol, param_dict)

            err.append(numpy.abs(sg - res) / stderr)

        return err
