# Single Cell Optimization

## Introduction

This documentation outlines how to setup distributed single cell optimization
using [eFEL](https://github.com/BlueBrain/eFEL), [DEAP](http://deap.readthedocs.org/en/master/)
and [SCOOP](scoop.readthedocs.org) along with [NEURON](www.neuron.yale.edu).

The scope of this documentation is on setup, not on the process of
optimization.

## Setup

The three sorts of distributed systems that this documentation targets are:

1. [Vagrant](https://www.vagrantup.com/) machines, usually used for testing
  as all the machines likely run on one local machine.  Detailed
  information [here](config/vagrant/README.md).

2. A cluster with a shared filesystem.  The optimization is configured
  within the home directory of the user such that it can be launched by
  [SLURM](https://computing.llnl.gov/linux/slurm/) or another cluster
  resource manager.  Detailed information [here](config/cluster-user/README.md).

3. An [Amazon Web Services](https://aws.amazon.com/) Detailed
  information [here](config/amazon/README.md).


## Ansible

Throughout this guide, [Ansible](http://www.ansible.com/) is used for the
automatic installation and configuration of the required software.

It is recommended to install it into a [Virtualenv](https://virtualenv.readthedocs.org/en/latest/)
so as to separate it from the rest of the system.
```
$ virtualenv venv-ansible
$ ./venv-ansible/bin/pip install ansible
```

From then on, one can activate the environment, and have access to Ansible:
```
$ source ./venv-ansible/bin/activate
$ ansible-playbook --version
```

Note: Ansible is not required, and all the commands can be run manually by
examining the `roles/*/tasks/main.yaml` files.


## Ansible Information

The three sorts of configurations share [Ansible Roles](http://docs.ansible.com/ansible/playbooks_roles.html#roles) but have different configuration information and parameters.

The easiest way to setup one of the three systems is to:

1. Change to the correct directory (`config/vagrant`, `config/cluster-user/`, or
   `config/amazon/`) and create a symbolic link to the `roles` directory:

   `$ ln -s ../../roles .`

2. Change any config information in `ansible.cfg` and `vars.yaml`

3. Edit the `hosts` file to include the correct hosts (in the Amazon case,
   this is handled by the `gather_config.py` script.


## Ansible configuration options

The following options are defined in the `vars.yaml` file, which should
contain the only options that could potentially need configuration.  They are:

- *user_name*: the name of the user under who's name the install will be run
- *workspace*: the base directory of the installation
- *venv*: the location of the virtualenvironment
- *build_dir*: the location where software is built
- *install_dir*: the base location where software is installed
- *add_bin_path*: Boolean on if the path to neuron and the python environment
 should be added to the users' `.bashrc`
- *using_headnode*: Set to true when there is a headnode that will control
  everything, used for when an SSH has to be distributed to the workers
- *neuron_build*: location to build NEURON
- *neuron_url*: URL to download the NEURON source
- *neuron_version*: NEURON version
- *neuron_config*: command to configure neuron
- *python27_build*: false - whether a local python version should be compiled
- *python27_url*: URL to get Python source
- *python27_version*: Python version

Versions for various python software that is installed
- *pip_version*: 7.1.2
- *numpy_version*: 1.10.4
- *efel_version*: 2.10.7
- *scoop_version*: 0.7.1.1
- *jupyter_version*: 1.0.0
- *matplotlib_version*: 1.5.1

## Installation Information

The installation is composed of several components:

1. Compiled version of NEURON in `~/workspace/install/nrnpython`.  This has
   the python bindings built in, and should also allow for dynamic loading of
   compiled `.modl` files

2. A python virtual environment with eFEL as well as DEAP and SCOOP.


## Ansible Tips

1. Test that your system is working and you can reach the hosts with `ansible -m ping all`

2. Use the 'Dry-run' command `ansible-playbook site.yml --check` to see what
   would happen if ansible was to run, this can be augmented with `--diff` to
   show differences

3. Use `-vv` and `-vvvv` to increase verbosity


## Running an Optimization Example

Note: Every optimization is different, this is an example on how to launch one
that already exists.

### eFEL Example

If there are multiple hosts, this has to be done on each of them.  If there is 
a shared file system, it only needs to be done once.
```
# Get latest eFEL
$ git clone https://github.com/BlueBrain/eFEL.git

# Compile the modl files with the nrnivmodl located in ~/workspace/install/. (for instance here ~/workspace/install/nrnpython/x86_64/bin/nrnivmodl)
$ cd ~/eFEL/examples/deap/GranuleCell1
$ ~/workspace/install/nrnpython/x86_64/bin/nrnivmodl mechanisms
```


#### Launch it:
Then, on the head node:
```
$ /home/neuron/workspace/venv/bin/python -m scoop -vvv --hostfile ~/scoop_workers GranuleCellDeap1-scoop.py
```
### DEAP Example

Get the [deap/examples/ga/onemax_island_scoop.py](https://github.com/DEAP/deap/blob/master/examples/ga/onemax_island_scoop.py) example.  You may want to
have it output data by editing the call to main with:

```
islands = main()
with open('output.dat', 'w') as fd:
    fd.write(str(islands))
    fd.write('\n')
```

Then, distribute it to all the worker nodes, if the node are not sharing their file system:
    (as the 'neuron' user: 'sudo su neuron')
```
    $ cd workspace
    $ for host in `cat ~/scoop_workers`; do scp onemax_island_scoop.py $i:workspace; done
```

#### Launch it:
```
    $ cd workspace
    $ venv/bin/python -m scoop --hostfile ~/scoop_workers onemax_island_scoop.py
    $ look at the output in 'output.dat'
```
