#!/bin/bash

cd bluepyopt/tests

declare -a StringArray=("./" "test_ephys/" "test_deapext/" )

for dir in ${StringArray[@]}
do
    touch ${dir}__init__.py
    sed -i'' 's/^import utils/from . import utils/g' $dir*.py
    sed -i'' 's/import testmodels.dummycells/from .testmodels import dummycells/g' $dir*.py
    sed -i'' 's/testmodels.dummycells/dummycells/g' $dir*.py
    sed -i'' 's/from deapext_test_utils import make_mock_population/from .deapext_test_utils import make_mock_population/g' $dir*.py
    sed -i'' 's/nt.assert_raises/pytest.raises/g' $dir*.py
    sed -i'' 's/nt.ok_/nt.assert_true/g' $dir*.py
    sed -i'' 's/nt.eq_/nt.assert_equal/g' $dir*.py
    sed -i'' 's/nt.assert/assert/g' $dir*.py
    sed -i'' 's/assert_almost_equal/numpy.testing.assert_almost_equal/g' $dir*.py
    sed -i'' 's/@nt.raises(Exception)/@pytest.mark.xfail(raises=Exception)/g' $dir*.py
    # sed -i'' 's/import nose.tools as nt/from . import assert_helpers/g' $dir*.py
    sed -i'' 's/import nose.tools as nt//g' $dir*.py
    sed -i'' 's/from nose.plugins.attrib import attr/import pytest\nimport numpy/g' $dir*.py
    sed -i'' "s/@attr('unit')/@pytest.mark.unit/g" $dir*.py
    sed -i'' "s/@attr('slow')/@pytest.mark.slow/g" $dir*.py
    # cp ../../assert_helpers.py $dir    
done

nose2pytest -v .
