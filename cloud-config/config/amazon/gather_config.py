#!/usr/bin/env python
import argparse

import boto3
from jinja2 import Environment


KEY_NAME = 'single_cell_opt.pem'
HEAD_INSTANCE_NAME = 'single_cell_opt_head'
WORKER_INSTANCE_NAME = 'single_cell_opt_worker'


hosts_template = '''
[neuron-optimizer-head]
{{ head_public_ip }}

[neuron-optimizer-worker]
{% for ip in worker_private_ips %}
{{ ip }}{% endfor %}
'''


ssh_config_template = '''
ControlMaster auto
ControlPersist 60s

Host 10.0.0.*
  ProxyCommand ssh -i {{ private_key }} -W %h:%p %r@{{ head_public_ip }}
'''


def _get_instances_by_tag(ec2, tag):
    '''filter on all instances, and get the ones tagged with 'type: tag' '''
    filters = [{'Name': 'tag:type', 'Values': [tag]},
               {'Name': 'instance-state-name', 'Values': ['running']},
               ]
    return list(ec2.instances.filter(Filters=filters))


def get_head_public_ip(ec2):
    '''returns string value of the public IP of the head instance'''
    instance = _get_instances_by_tag(ec2, HEAD_INSTANCE_NAME)
    assert len(instance) == 1, 'Only expect one head node'
    instance = instance[0]
    return instance.public_ip_address


def get_work_private_ips(ec2, tag=WORKER_INSTANCE_NAME, include_head=True):
    '''get the internal IPs of the workers, including the head by default'''
    instances = _get_instances_by_tag(ec2, tag)
    if include_head:
        head_instance = _get_instances_by_tag(ec2, HEAD_INSTANCE_NAME)
        assert len(head_instance) == 1, 'Only expect one head node'
        head_ip = head_instance[0].private_ip_address
    return [head_ip] + [i.private_ip_address for i in instances]


def get_parser():
    '''return the argument parser'''
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--dry-run', action='store_true',
        help='Output the results of the templates without writing them')
    return parser


def main():
    '''main function'''
    args = get_parser().parse_args()

    ec2 = boto3.resource('ec2')

    print('Instances:', list(i.id for i in ec2.instances.all()))

    env = Environment()
    hosts = env.from_string(hosts_template)
    ssh_config = env.from_string(ssh_config_template)

    head_public_ip = get_head_public_ip(ec2)
    worker_private_ips = get_work_private_ips(ec2)

    hosts_rendered = hosts.render(head_public_ip=head_public_ip,
                                  worker_private_ips=worker_private_ips)

    ssh_config_rendered = ssh_config.render(head_public_ip=head_public_ip,
                                            private_key=KEY_NAME)

    if args.dry_run:
        print('{:*^30}'.format(' Hosts '))
        print(hosts_rendered)
        print('{:*^30}'.format(' ssh_config '))
        print(ssh_config_rendered)
    else:
        with open('hosts', 'w') as fd:
            fd.write(hosts_rendered)
        with open('amazon_ssh_config', 'w') as fd:
            fd.write(ssh_config_rendered)


if __name__ == '__main__':
    main()
