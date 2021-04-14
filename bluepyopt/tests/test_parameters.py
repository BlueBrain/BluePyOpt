"""bluepyopt.parameters tests"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# pylint:disable=W0612


import pytest

import bluepyopt


@pytest.mark.unit
def test_parameters_init():
    """bluepyopt.parameters: test Parameter init"""

    param = bluepyopt.parameters.Parameter(name='test')
    assert isinstance(param, bluepyopt.parameters.Parameter)
    assert param.name == 'test'


@pytest.mark.unit
def test_parameters_fields():
    """bluepyopt.parameters: test Parameter fields"""

    param = bluepyopt.parameters.Parameter(name='test')

    assert param.lower_bound is None
    assert param.upper_bound is None

    param.freeze(5)
    pytest.raises(Exception, setattr, param, "value", 5)

    param = bluepyopt.parameters.Parameter(name='test', bounds=[2, 5])
    pytest.raises(ValueError, param.freeze, 1)


@pytest.mark.unit
def test_parameters_str():
    """bluepyopt.parameters: test Parameter str conversion"""

    param = bluepyopt.parameters.Parameter(name='test')

    assert str(param) == 'test: value = None'

    param.freeze(5.5)

    assert str(param) == 'test: value = 5.5'


@pytest.mark.unit
def test_MetaListEqualParameter_init():
    """bluepyopt.parameters: test MetaListEqualParameter init"""

    sub_params = [
        bluepyopt.parameters.Parameter(
            name='sub1', value=1), bluepyopt.parameters.Parameter(
            name='sub2', value=2)]

    assert sub_params[0].value == 1
    assert sub_params[1].value == 2

    param = bluepyopt.parameters.MetaListEqualParameter(
        name='param', value=0, frozen=True, sub_parameters=sub_params)
    assert isinstance(param, bluepyopt.parameters.Parameter)
    assert isinstance(param, bluepyopt.parameters.MetaListEqualParameter)

    assert param.name == 'param'
    assert param.sub_parameters[0].name == 'sub1'
    assert param.sub_parameters[1].name == 'sub2'

    assert param.value == 0
    assert sub_params[0].value == 0
    assert sub_params[1].value == 0


@pytest.mark.unit
def test_MetaListEqualParameter_freeze_unfreeze():
    """bluepyopt.parameters: test MetaListEqualParameter freeze and unfreeze"""

    sub_params = [
        bluepyopt.parameters.Parameter(
            name='sub1', value=1), bluepyopt.parameters.Parameter(
            name='sub2', value=2)]

    param = bluepyopt.parameters.MetaListEqualParameter(
        name='param', sub_parameters=sub_params)

    assert param.value is None
    assert sub_params[0].value == 1
    assert sub_params[1].value == 2

    param.freeze(0)

    assert param.value == 0
    assert sub_params[0].value == 0
    assert sub_params[1].value == 0

    param.unfreeze()

    sub_params[0].freeze(1)
    pytest.raises(Exception, param.freeze, 0)


@pytest.mark.unit
def test_MetaListEqualParamete_str():
    """bluepyopt.parameters: test MetaListEqualParamete str conversion"""

    sub_params = [
        bluepyopt.parameters.Parameter(
            name='sub1', value=1), bluepyopt.parameters.Parameter(
            name='sub2', value=2)]

    param = bluepyopt.parameters.MetaListEqualParameter(
        name='param', sub_parameters=sub_params)

    assert (
        str(param)
        == 'param (sub_params: sub1: value = None,sub2: value = None): '
        'value = None')

    param.freeze(5.5)

    assert (
        str(param)
        == 'param (sub_params: sub1: value = 5.5,sub2: value = 5.5): '
        'value = 5.5')
