"""bluepy.ephys test"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

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

import nose.tools as nt
from nose.plugins.attrib import attr


@attr('unit')
def test_import():
    """ephys: test importing bluepyopt.ephys"""
    import bluepyopt.ephys  # NOQA


@attr('unit')
def test_ephys_base():
    """ephys: test ephys base class"""
    import bluepyopt.ephys as ephys
    base = ephys.base.BaseEPhys(name='test', comment='comm')

    nt.assert_equal(str(base), 'BaseEPhys: test (comm)')
