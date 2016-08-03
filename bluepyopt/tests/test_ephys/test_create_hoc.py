import utils
from bluepyopt.ephys import create_hoc

import nose.tools as nt


def test__generate_channels_by_location():
    mech = utils.make_mech()
    channels = create_hoc._generate_channels_by_location([mech, ])

    nt.eq_(len(channels['apical']), 1)
    nt.eq_(len(channels['basal']), 1)

    nt.eq_(channels['apical'], ['Ih'])
    nt.eq_(channels['basal'], ['Ih'])


def test__generate_parameters():
    parameters = utils.make_parameters()

    global_params, section_params, range_params = \
        create_hoc._generate_parameters(parameters)

    nt.eq_(global_params, {'NrnGlobalParameter': 65})
    nt.eq_(len(section_params[1]), 2)
    nt.eq_(len(section_params[4]), 2)
    nt.eq_(section_params[4][0], 'somatic')
    nt.eq_(len(section_params[4][1]), 2)


def test_create_hoc():
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    hoc = create_hoc.create_hoc([mech, ], parameters, template_name='CCell')
    nt.ok_('load_file' in hoc)
    nt.ok_('CCell' in hoc)
    nt.ok_('begintemplate' in hoc)
    nt.ok_('endtemplate' in hoc)
