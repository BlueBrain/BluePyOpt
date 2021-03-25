apt-get update
apt-get install -y gcc
apt-get install -y libx11-6 python-dev git build-essential
apt-get install -y autoconf automake g++ make gfortran
apt-get install -y python-tables
# for hdf5 allensdk
apt-get install -y libhdf5-serial-dev
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
conda config --set always_yes yes --set changeps1 no
conda update -q --all
conda config --add channels conda-forge
conda config --set always_yes true
conda config --set quiet true
conda install conda-build
conda install scipy;
conda install numpy;
conda install numba;
conda install dask;
