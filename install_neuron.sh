#!/bin/sh

set -e

SRC_DIR=$1
INSTALL_DIR=$2
#PYTHON_BIN=$3
PYTHON_BIN="$(which python)"

if [ ! -e ${INSTALL_DIR}/.install_finished ]
then
    echo 'Neuron was not fully installed in previous build, installing ...'
    mkdir -p ${SRC_DIR}
    cd ${SRC_DIR}
    echo "Downloading NEURON ..."
    rm -rf nrn
	git clone --depth 1 https://github.com/neuronsimulator/nrn.git >download.log 2>&1
	cd nrn
    echo "Preparing NEURON ..."
	./build.sh >prepare.log 2>&1
    echo "Configuring NEURON ..."

    PYTHON_BLD=${PYTHON_BIN} ./configure --prefix=${INSTALL_DIR} --without-x --with-nrnpython=${PYTHON_BIN} --disable-rx3d >configure.log 2>&1
    echo "Building NEURON ..."
    make -j4 #>make.log 2>&1
    #cat make.log
    echo "Installing NEURON ..."
    make -j4 install #>install.log 2>&1
    #cat install.log
    #export PATH="${INSTALL_DIR}/x86_64/bin":${PATH}
    #export PYTHONPATH="${INSTALL_DIR}/lib/python":${PYTHONPATH}
    #${PYTHON_BIN} -c "import neuron"
    #${PYTHON_BIN}-c "from neuron import h"


    #echo "Testing NEURON import ...."
    #${PYTHON_BIN} -c 'import neuron' >testimport.log 2>&1
    #touch -f ${INSTALL_DIR}/.install_finished
    #echo "NEURON successfully installed"
else
    echo 'Neuron was successfully installed in previous build, not rebuilding'
fi
