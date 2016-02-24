"""Create tables for BluePyOpt paper"""

import json


def load_json(filename):
    """Load struct from json"""

    return json.load(open(filename))


def create_feature_fields():
    """Create fields for param.json"""

    features = json.load(open('features.json'))

    fields_content = ''

    print features

    fields_content += \
        '\t\t\tStimulus & Location & eFeature & Mean & Std \\\\ \n'
    fields_content += '\t\t\t\midrule\n'
    for stimulus, loc_list in sorted(features.iteritems()):
        stim_field = stimulus
        for location, features in sorted(loc_list.iteritems()):
            loc_field = location
            for feature_name, (mean, std) in sorted(features.iteritems()):
                feature_name = feature_name.replace('_', '{\_}')
                fields_content += '\t\t\t%s \\\\\n' % ' & '.join([stim_field,
                                                                 loc_field,
                                                                 feature_name,
                                                                 str(mean),
                                                                 str(std)])
                if loc_field is not '':
                    loc_field = ''
                if stim_field is not '':
                    stim_field = ''
    fields_content += '\t\t\t\\botrule\n'

    return fields_content


def create_param_fields():
    """Create fields for param.json"""

    params = json.load(open('params.json'))

    fields_content = ''
    fields_content += \
        '\t\t\tLocation & Mechanism & Parameter name & ' \
        'Lower bound & Upper bound \\\\\n'
    fields_content += '\t\t\t\midrule\n'
    for section_list, param_list in sorted(params.iteritems()):
        section_field = section_list
        for prefix, param_name, min, max, distribution in param_list:
            prefix = prefix.replace('_', '{\_}')
            param_name = param_name.replace('_', '{\_}')
            fields_content += '\t\t\t%s \\\\\n' % ' & '.join([section_field,
                                                             prefix,
                                                             param_name,
                                                             str(min),
                                                             str(max)])
            if section_field is not '':
                section_field = ''
    fields_content += '\t\t\t\\botrule\n'

    return fields_content


def create_table(field_content):
    """Surround fiels with table creation"""

    table_content = '\processtable{ } {\n\t\\begin{tabular}{lllll}\\toprule\n'

    table_content += field_content

    table_content += '\n\t\end{tabular}\n}'

    return table_content


def main():
    """Main"""

    param_fields = create_param_fields()
    param_content = create_table(param_fields)
    open('tables/params.tex', 'w').write(param_content)
    print param_content

    feature_fields = create_feature_fields()
    feature_content = create_table(feature_fields)
    open('tables/features.tex', 'w').write(feature_content)
    print feature_content

if __name__ == '__main__':
    main()
