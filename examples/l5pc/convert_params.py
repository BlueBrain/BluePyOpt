"""Convert params.json and fixed_params.json to parameters.json format"""

from __future__ import print_function

import json


def main():
    """Main"""

    fixed_params = json.load(open('fixed_params.json'))
    params = json.load(open('params.json'))

    parameters = []

    for sectionlist in fixed_params:
        if sectionlist == 'global':
            for param_name, value in fixed_params[sectionlist]:
                param = {
                    'value': value,
                    'param_name': param_name,
                    'type': 'global'}
                parameters.append(param)
        else:
            for param_name, value, dist_type in fixed_params[sectionlist]:
                param = {
                    'value': value,
                    'param_name': param_name,
                    'type': 'section',
                    'dist_type': dist_type,
                    'sectionlist': sectionlist
                }
                parameters.append(param)

    for sectionlist in params:
        for mech, param_name, min_bound, max_bound, dist_type in \
                params[sectionlist]:
            param = {
                'bounds': [min_bound, max_bound],
                'mech': mech,
                'mech_param': param_name,
                'param_name': '%s_%s' % (param_name, mech),
                'type': 'range',
                'dist_type': dist_type,
                'sectionlist': sectionlist
            }

            if mech == 'Ih':
                del param['bounds']
                param['value'] = 8e-5

            if dist_type == 'exp':
                param['dist'] = \
                    '(-0.8696 + 2.087*math.exp(({distance})*0.0031))*{value}'

            parameters.append(param)

    json.dump(parameters, open('parameters.json', 'w'),
              indent=4,
              separators=(',', ': '))

if __name__ == '__main__':
    main()
