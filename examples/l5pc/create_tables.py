"""Create tables for BluePyOpt paper"""

import json


def load_json(filename):
    """Load struct from json"""

    return json.load(open(filename))


def create_feature_fields():
    """Create fields for param.json"""

    features = json.load(open('features.json'))

    fields_content = ''

    print(features)

    fields_content += \
        '\t\tStimulus & Location & eFeature & Mean & Std \\\\ \n'
    fields_content += '\t\t\\midrule\n'
    for stimulus, loc_list in sorted(features.items()):
        stim_field = stimulus
        for location, features in sorted(loc_list.items()):
            loc_field = location
            for feature_name, (mean, std) in sorted(features.items()):
                feature_name = feature_name.replace('_', '{\\_}')
                fields_content += '\t\t%s \\\\\n' % ' & '.join([stim_field,
                                                                loc_field,
                                                                feature_name,
                                                                str(mean),
                                                                str(std)])
                if loc_field != '':
                    loc_field = ''
                if stim_field != '':
                    stim_field = ''
    fields_content += '\t\t\\botrule\n'

    return fields_content, 6


def create_param_fields_list():
    """Create fields for param.json"""

    import collections
    param_configs = json.load(open('parameters.json'))

    fields_list = []
    for param_config in param_configs:
        fields = collections.OrderedDict(
            (('location', ''),
             ('mech', ''),
             ('param', ''),
             ('dist', ''),
             ('units', ''),
             ('lbound', ''),
             ('ubound', ''),
             ('value', '')))

        if 'value' in param_config:
            fields['value'] = str(param_config['value'])
        elif 'bounds' in param_config:
            fields['lbound'] = str(param_config['bounds'][0])
            fields['ubound'] = str(param_config['bounds'][1])

        if param_config['type'] == 'global':
            fields['param'] = param_config['param_name']
            fields['location'] = 'global'
        elif param_config['type'] in ['section', 'range']:
            fields['dist'] = param_config['dist_type']
            fields['location'] = param_config['sectionlist']
            if param_config['type'] == 'range':
                fields['mech'] = param_config['mech']
                fields['param'] = param_config['mech_param']
            elif param_config['type'] == 'section':
                fields['param'] = param_config['param_name']

        if 'bar' in fields['param'] or fields['param'] == 'g_pas':
            fields['units'] = '\\SI{}{\\siemens\\per\\cm\\squared}'
        elif fields['param'] == 'gamma':
            fields['units'] = ''
        elif fields['param'] == 'decay':
            fields['units'] = ' \\SI{}{\\milli\\second}'
        elif 'celsius' == fields['param']:
            fields['units'] = ' \\SI{}{\\celsius}'
        elif fields['param'] in ['v_init', 'e_pas', 'ek', 'ena']:
            fields['units'] = ' \\SI{}{\\milli\\volt}'
        elif 'Ra' == fields['param']:
            fields['units'] = ' \\SI{}{\\ohm\\cm}'
        elif 'cm' == fields['param']:
            fields['units'] = ' \\SI{}{\\micro\\farad\\per\\cm\\squared}'

        for key in fields:
            fields[key] = fields[key].replace('_', '{\\_}')

        fields_list.append(fields)

    return fields_list


def create_param_fields_string():
    """Create parameter fields string"""

    fields_list = create_param_fields_list()

    fields_content = ''
    fields_content += \
        '\t\tLocation & Mechanism & Parameter name & ' \
        'Distribution & Units & Lower bound & Upper bound \\\\\n'
    fields_content += '\t\t\\midrule\n'

    opt_fields = [field for field in fields_list if field['value'] == '']
    fixed_fields = [field for field in fields_list if field['value'] != '']
    global_fixed_fields = [
        field
        for field in fixed_fields if field['location'] == 'global']
    nonglobal_fixed_fields = [
        field
        for field in
        fixed_fields if field['location'] != 'global']

    for fields in opt_fields:
        del fields['value']
        fields_content += '\t\t%s \\\\\n' % ' & '.join(fields.values())
    fields_content += '\t\t\\midrule\n'
    fields_content += \
        '\t\tLocation & Mechanism & Parameter name & ' \
        'Distribution & Units & Value & \\\\\n'
    fields_content += '\t\t\\midrule\n'
    for fields in global_fixed_fields + nonglobal_fixed_fields:
        del fields['lbound']
        del fields['ubound']
        fields_content += '\t\t%s \\\\\n' % ' & '.join(
            fields.values() + [' '])

    fields_content += '\t\t\\botrule\n'

    return fields_content, 7


def create_table(field_content, n_of_cols):
    """Surround fiels with table creation"""

    table_content = '\\begin{tabular}{%s}\n\t\\toprule\n' % \
        ('l' * n_of_cols)

    table_content += field_content

    table_content += '\n\\end{tabular}'

    return table_content


def main():
    """Main"""

    param_fields, n_of_cols = create_param_fields_string()
    param_content = create_table(param_fields, n_of_cols)
    open('tables/params.tex', 'w').write(param_content)
    print(param_content)

    feature_fields, n_of_cols = create_feature_fields()
    feature_content = create_table(feature_fields, n_of_cols)
    open('tables/features.tex', 'w').write(feature_content)
    print(feature_content)


if __name__ == '__main__':
    main()
