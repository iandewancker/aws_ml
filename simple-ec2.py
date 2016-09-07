#!/usr/bin/env python
'''
Before using be sure to set AWS_KEY and AWS_SECRET_KEY environment vars, e.g.:
export AWS_KEY=<YOUR_AWS_KEY>
export AWS_SECRET_KEY=<YOUR_AWS_SECRET_KEY>

# create cluster (using on-demand or spot instances)
simple-ec2 --key ian --type t2.medium --num 2 --region us-west-2 create ian-test
simple-ec2 --key ian --type t2.medium --price 0.50 --num 2 --region us-west-2 create-spot ian-test

# stop / start / destroy cluster
simple-ec2 stop ian-test

# run bash or python script on all cluster instances 
# (copies script to instances, overwriting existing versions on all instances)
simple-ec2 -i ian_aws.pem run ian-test ./exp.py 

# kill running scripts on all cluster instances
simple-ec2 -i ian_aws.pem kill ian-test

# copy file to all cluster instances
simple-ec2 -i ian_aws.pem copy ian-test test_file.txt 

# list instance details
simple-ec2 describe ian-test
'''

import boto.ec2
import copy as cp
import os
import argparse
import sys
import time
import scp
import subprocess

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def copy(args):
	# check for identity file
	if args.i is None:
		print bcolors.FAIL + "No identity file (.pem) provided! (please provide -i argument)"+ bcolors.ENDC
		sys.exit(1)

	conn = boto.ec2.connect_to_region(args.region,
		aws_access_key_id=os.environ.get('AWS_KEY'),
		aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	# for every instance, scp script over to machine with replacement
	for instance in clust_instances:
		scp_cmd = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i \
			{0} {1} ubuntu@{2}:".format(args.i, args.script,instance.public_dns_name)
		subprocess.check_output(scp_cmd, shell=True, stderr=subprocess.STDOUT)
		print bcolors.OKGREEN + "SCP "+ bcolors.ENDC + args.script + bcolors.OKGREEN +" to " + bcolors.ENDC + instance.public_dns_name


def run(args):
	# check for identity file
	if args.i is None:
		print bcolors.FAIL + "No identity file (.pem) provided! (please provide -i argument)"+ bcolors.ENDC
		sys.exit(1)

	conn = boto.ec2.connect_to_region(args.region,
		aws_access_key_id=os.environ.get('AWS_KEY'),
		aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	# for every instance, scp script over to machine with replacement
	for instance in clust_instances:
		scp_cmd = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i \
			{0} {1} ubuntu@{2}:".format(args.i, args.script,instance.public_dns_name)
		subprocess.check_output(scp_cmd, shell=True, stderr=subprocess.STDOUT)
		print bcolors.WARNING + "SCP "+ bcolors.ENDC + args.script + bcolors.WARNING +" to " + bcolors.ENDC + instance.public_dns_name

		# start tmux session  and launch script on each machine
		#tmux_cmd = "tmux new-session -d -s {0} 'python {1}'".format(args.cluster_name, args.script)
		if ".py" in args.script:
			tmux_cmd = "\"tmux new-session -d -s {0} \'python {1}\'\"".format(args.cluster_name, args.script)
		elif ".sh" in args.script:
			tmux_cmd = "\"tmux new-session -d -s {0} \'bash {1}\'\"".format(args.cluster_name, args.script)
		else:
			print bcolors.FAIL + "Please provide either python (.py) or bash (.sh) script file"+ bcolors.ENDC

		subprocess.check_output("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i \
			{0} ubuntu@{1} {2}".format(args.i, instance.public_dns_name, tmux_cmd), shell=True,
			stderr=subprocess.STDOUT)
		print bcolors.OKGREEN + "TMUX "+ bcolors.ENDC + args.script + bcolors.OKGREEN +" on " + bcolors.ENDC + instance.public_dns_name

def kill(args):
	# check for identity file
	if args.i is None:
		print bcolors.FAIL + "No identity file (.pem) provided! (please provide -i argument)"+ bcolors.ENDC
		sys.exit(1)

	conn = boto.ec2.connect_to_region(args.region,
		aws_access_key_id=os.environ.get('AWS_KEY'),
		aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	# for every instance, kill tmux session
	tmux_cmd = "\"tmux kill-session -t {0}\"".format(args.cluster_name)
	for instance in clust_instances:
		subprocess.check_output("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i \
			{0} ubuntu@{1} {2}".format(args.i, instance.public_dns_name, tmux_cmd), shell=True,
			stderr=subprocess.STDOUT)
		print bcolors.FAIL + "KILLED TMUX on " + bcolors.ENDC + instance.public_dns_name

def create_spot(args):
	# establish AWS connection
	conn = boto.ec2.connect_to_region(args.region,
		aws_access_key_id=os.environ.get('AWS_KEY'),
		aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	# Check for name collision
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	prev_clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	if prev_clust_instances:
		print bcolors.WARNING + "Previous instances for cluster : "+ bcolors.ENDC + args.cluster_name + bcolors.WARNING +" exist!" + bcolors.ENDC
		print bcolors.FAIL + str(prev_clust_instances) + bcolors.ENDC
		sys.exit(1)

	# create request for spot instances
	print bcolors.WARNING + "Creating spot instances ..." + bcolors.ENDC
	spot_requests = conn.request_spot_instances(args.price, args.ami, count=args.num, type='one-time', 
		instance_type=args.type, key_name=args.key, security_group_ids=[args.secgroup])
	time.sleep(10)
	# Figure out what our spot request ids are
	request_ids = [req.id for req in spot_requests]
	pending_request_ids = cp.deepcopy(request_ids)
	created_instance_ids = []
	num_fails = 0
	# Wait for 
	while True:
		results = conn.get_all_spot_instance_requests(request_ids=pending_request_ids)
		for result in results:
			if result.status.code == 'fulfilled':
				pending_request_ids.pop(pending_request_ids.index(result.id))
				#print dir(result)
				# set the Name and Cluster tag on the instances
				print "spot request `{}` fulfilled!".format(result.id)

				print result.instance_id + " created!"
				conn.create_tags([result.instance_id], {"Name": args.cluster_name+'-'+result.instance_id})
				conn.create_tags([result.instance_id], {"Cluster": args.cluster_name})
				created_instance_ids.append(result.instance_id)
			else:
				print "waiting on `{}`".format(result.id)

		if len(pending_request_ids) == 0:
			print "all spots fulfilled!"
			break
		else:
			time.sleep(10)
		
		# set reasonable time out
		num_fails += 1
		if num_fails == 10:
			print bcolors.FAIL + "Attempts to create spot instances failed too many times ..." + bcolors.ENDC
			print bcolors.WARNING + "Consider setting --price higher than :" + bcolors.ENDC, args.price
			# kill request if failed too many times
			conn.cancel_spot_instance_requests(request_ids)
			# kill all created instances as well
			if created_instance_ids:
				conn.terminate_instances(instance_ids=created_instance_ids)
			sys.exit(1)
	
	# blocking loop while machines start until they have DNS
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	all_instance_ids = set([i.id for i in clust_instances])
	active_instance_ids = set([])
	print bcolors.WARNING + "Waiting for instances to initialize ..." + bcolors.ENDC
	while True:
		clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
		clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
		for instance in clust_instances:
			status = conn.get_all_instance_status(instance_ids=[instance.id])
			instance_reachable = False
			if status:
				reachability = status[0].system_status.details['reachability']
				instance_reachable = (reachability == 'passed')

			# instance is provisioned and can be ssh'd to
			if instance.id not in active_instance_ids and instance.public_dns_name is not None and instance.state =='running' and instance_reachable:
				print instance.tags['Name'], instance.public_dns_name, bcolors.OKGREEN + instance.state + bcolors.ENDC
				active_instance_ids.add(instance.id)
		if active_instance_ids == all_instance_ids:
			break
		time.sleep(10)


# helper method to create cluster and provide output to user
def create(args):
	# establish AWS connection
	conn = boto.ec2.connect_to_region(args.region,
		aws_access_key_id=os.environ.get('AWS_KEY'),
		aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	# Check for name collision
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	prev_clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	if prev_clust_instances:
		print bcolors.WARNING + "Previous instances for cluster : "+ bcolors.ENDC + args.cluster_name + bcolors.WARNING +" exist!" + bcolors.ENDC
		print bcolors.FAIL + str(prev_clust_instances) + bcolors.ENDC
		sys.exit(1)

	# create reservation for cluster
	reservation = conn.run_instances(args.ami, min_count=args.num, max_count=args.num, 
		key_name=args.key, instance_type=args.type, security_group_ids=[args.secgroup])
	# generate name and cluster tags for instances
	for instance in reservation.instances:
		conn.create_tags([instance.id], {"Name": args.cluster_name+'-'+instance.id})
		conn.create_tags([instance.id], {"Cluster": args.cluster_name})

	# blocking loop while machines start until they have DNS
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	all_instance_ids = set([i.id for i in clust_instances])
	active_instance_ids = set([])
	print bcolors.WARNING + "Creating instances ..." + bcolors.ENDC
	while True:
		clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
		clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
		for instance in clust_instances:
			status = conn.get_all_instance_status(instance_ids=[instance.id])
			instance_reachable = False
			if status:
				reachability = status[0].system_status.details['reachability']
				instance_reachable = (reachability == 'passed')

			# instance is provisioned and can be ssh'd to
			if instance.id not in active_instance_ids and instance.public_dns_name is not None and instance.state =='running' and instance_reachable:
				print instance.tags['Name'], instance.public_dns_name, bcolors.OKGREEN + instance.state + bcolors.ENDC
				active_instance_ids.add(instance.id)
		if active_instance_ids == all_instance_ids:
			break
		time.sleep(10)

def hosts(args):
	conn = boto.ec2.connect_to_region(args.region,
	aws_access_key_id=os.environ.get('AWS_KEY'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	for instance in clust_instances:
		print instance.public_dns_name
		

def stop(args):
	conn = boto.ec2.connect_to_region(args.region,
	aws_access_key_id=os.environ.get('AWS_KEY'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances_ids = [i.id for r in clust_reservations for i in r.instances if i.state != 'terminated']
	
	conn.stop_instances(instance_ids=clust_instances_ids)

	print bcolors.WARNING + "Stopping instances ..." + bcolors.ENDC
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	for instance in clust_instances:
		print instance.tags['Name'], instance.public_dns_name, bcolors.FAIL + instance.state + bcolors.ENDC		

def start(args):
	conn = boto.ec2.connect_to_region(args.region,
	aws_access_key_id=os.environ.get('AWS_KEY'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances_ids = [i.id for r in clust_reservations for i in r.instances if i.state != 'terminated']
	
	conn.start_instances(instance_ids=clust_instances_ids)

	print bcolors.WARNING + "Starting instances ..." + bcolors.ENDC
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	for instance in clust_instances:
		print instance.tags['Name'], instance.public_dns_name, bcolors.OKGREEN + instance.state + bcolors.ENDC	


def describe(args):
	conn = boto.ec2.connect_to_region(args.region,
	aws_access_key_id=os.environ.get('AWS_KEY'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	for instance in clust_instances:
		status = conn.get_all_instance_status(instance_ids=[instance.id])
		value = "not reachable"
		if status:
			value = status[0].system_status.details['reachability']
		reach = "reachability : "+value
		if instance.state != 'running':
			print instance.tags['Name'], instance.public_dns_name, bcolors.WARNING + instance.state + bcolors.ENDC, reach
		else:
			print instance.tags['Name'], instance.public_dns_name, bcolors.OKGREEN + instance.state + bcolors.ENDC, reach

def destroy(args):
	conn = boto.ec2.connect_to_region(args.region,
	aws_access_key_id=os.environ.get('AWS_KEY'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	# destroy all instances in cluster: args.cluster_name
	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances_ids = [i.id for r in clust_reservations for i in r.instances if i.state != 'terminated']
	if not clust_instances_ids:
		print bcolors.WARNING + "No active instances for cluster : '"+args.cluster_name+"' remain!" + bcolors.ENDC
		sys.exit(1)  
	
	conn.terminate_instances(instance_ids=clust_instances_ids)

	clust_reservations = conn.get_all_instances(filters={"tag:Cluster" : args.cluster_name})
	clust_instances = [i for r in clust_reservations for i in r.instances if i.state != 'terminated']
	print bcolors.WARNING + "Terminating instances ..." + bcolors.ENDC
	for instance in clust_instances:
		print instance.tags['Name'], instance.public_dns_name, bcolors.FAIL + instance.state + bcolors.ENDC


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--ami',
		help='AWS AMI id to be used in cluster (e.g. ami-9abea4fb)',
		type=str,
		required=False,
		default='ami-9abea4fb',	
	)

	parser.add_argument(
		'--key',
		help='AWS keypair name',
		type=str,
		required=False,
		default=None,	
	)

	parser.add_argument(
		'--secgroup',
		help='AWS security group (e.g. \'sg-56ca3e31\')',
		type=str,
		required=False,
		default='sg-56ca3e31',	
	)

	parser.add_argument(
		'--type',
		help='EC2 instance type (e.g. t2.medium)',
		type=str,
		required=False,
		default='t2.medium',	
	)

	parser.add_argument(
		'--num',
		help='Number of EC2 instances in cluster',
		type=int,
		required=False,
		default=2,	
	)

	parser.add_argument(
		'--region',
		help='AWS region (e.g. us-west-2)',
		type=str,
		required=False,
		default='us-west-2',	
	)

	parser.add_argument(
		'--price',
		help='Bid price in dollars for spot instances (e.g. 0.52)',
		type=float,
		required=False,
		default=None,	
	)

	parser.add_argument(
		'-i',
		help='identity file (e.g. user.pem)',
		type=str,
		required=False,	
	)

	parser.add_argument('command', help='cluster command [create, run, copy, describe, stop, start, destroy, hosts]')
	parser.add_argument('cluster_name', help='cluster name (eg \'test-cluster\')')
	parser.add_argument('script', nargs='?',help='optional .sh or .py script for run cmd', default=None)
	args = parser.parse_args()

	if args.command == 'create':
		create(args)
	elif args.command == 'create-spot':
		create_spot(args)
	elif args.command == 'destroy':
		destroy(args)
	elif args.command == 'describe':
		describe(args)
	elif args.command == 'hosts':
		hosts(args)
	elif args.command == 'stop':
		stop(args)
	elif args.command == 'start':
		start(args)
	elif args.command == 'run':
		run(args)
	elif args.command == 'kill':
		kill(args)
	elif args.command == 'copy':
		copy(args)
