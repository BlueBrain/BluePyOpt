# Vagrant Setup

 1. Install vagrant

 2. Get the trusty64 box:

    `$ vagrant box add ubuntu/trusty64`

 3. Use the included `Vagrantfile` to bring up 4 machines:
    This includes:
      - *head*: 192.168.61.10
      - *worker0*: 192.168.61.20
      - *worker1*: 192.168.61.21
      - *worker2*: 192.168.61.22

 4. Boot the vagrant instances:

    `$ vagrant up`

## Configure with Ansible

Note: Make sure that there is a virtual environment from which you will run
`Ansible`, read the documentation [here](../../README.md) to set one up.

```
$ source ./venv-ansible/activate
$ ansible-playbook site.yaml
```

Notes:
 - `hosts.example` defines the host groups, and uses the running Vagrant instances.
 - `ansible.cfg` defines some defaults (like `hosts.example` and which ssh key to use)
 - One can `vagrant destroy` and then `vagrant up` to start from a clean slate
