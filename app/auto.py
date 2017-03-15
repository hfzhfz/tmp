#!/usr/bin/python

import time
import boto3
import mysql.connector
import math
from datetime import datetime, timedelta

db_config = {'user': 'root', 
             'password': 'ece1779pass',
             'host': '172.31.70.89',
             'cloudWatch': 'cloudWatch',
             'ami_id': 'ami-fdd77beb'}



def ec2_create():

	ec2 = boto3.resource('ec2')
	client = boto3.client('elb')

	instance = ec2.create_instances(
	        ImageId=db_config['ami_id'], 
	        MinCount=1, 
	        MaxCount=1,
	        KeyName='1779_key',
	        SecurityGroupIds=['sg-95976cea',],
	        InstanceType='t2.small',
	        Monitoring={'Enabled': True}
	        )
	
	value = 'ece1779worker'

	tag = instance[0].create_tags(
	    Tags=[
	        {
	            'Key': 'Name',
	            'Value': value
	        },
	    ]
	)
    
	response = client.register_instances_with_load_balancer(
	    LoadBalancerName='1779ELB',
	    Instances=[
	        {
	            'InstanceId': instance[0].id
	        },
	    ]
	)


def ec2_destroy(id):
    
	ec2 = boto3.resource('ec2')
	client = boto3.client('elb')

	response = client.deregister_instances_from_load_balancer(
	    LoadBalancerName='1779ELB',
	    Instances=[
	        {
	            'InstanceId': id
	        },
	    ]
	)

	ec2.instances.filter(InstanceIds=[id]).terminate()


def auto():
	#cnx = get_db()
	#cursor = cnx.cursor()
	ec2 = boto3.resource('ec2')
	cnx = mysql.connector.connect(host=db_config['host'],
								  user=db_config['user'],
								  password=db_config['password'],
								  database=db_config['cloudWatch'])
	cursor = cnx.cursor()

	client = boto3.client('cloudwatch')


	while(1):
		query = "SELECT * FROM workers WHERE id = %s"

		cursor.execute(query,(1,))

		row = cursor.fetchone()

		grow_ratio = row[1]
		shrink_ratio = row[2]
		grow_threshold = row[3]
		shrink_threshold = row[4]

		print("grow_ratio=" + str(grow_ratio))
		print("shrink_ratio=" + str(shrink_ratio))
		print("grow_threshold=" + str(grow_threshold))
		print("shrink_threshold=" + str(shrink_threshold))

		cnx.commit()

		metric_name = 'CPUUtilization'

		namespace = 'AWS/EC2'
		statistic = 'Maximum'                   

		cpu = client.get_metric_statistics(
		    Period=1 * 60,
		    StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
		    EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
		    MetricName=metric_name,
		    Namespace=namespace,  
		    Statistics=[statistic],
		    Dimensions=[{'Name': 'InstanceId', 'Value': 'i-0dd8069a3598ec8a5'}]
		)

		instances = ec2.instances.all()

		count = 0

		for instance in instances:
			if instance.state['Name'] == 'running':
				count += 1  #total number of running instances
		
		count -= 2 # number of running workers
		print("count=" +str(count))
		cpu_stats = []

		for point in cpu['Datapoints']:
			#print(point['Maximum'])
			cpu_stats.append(point['Maximum'])
		print(min(cpu_stats))

		if max(cpu_stats) > grow_threshold:
			times = (grow_ratio-1) * count
			for i in range(times):
				#print("I will create")
				ec2_create()
			
		elif (min(cpu_stats) < shrink_threshold and shrink_threshold < grow_threshold):
			worker_left = math.ceil(count / shrink_ratio)
			worker_destroy = count - worker_left
			instances = ec2.instances.all()
			#print(worker_destroy)
			for instance in instances:
				if(worker_destroy<1):
					break
				if not (instance.id == 'i-026f5969050b98d16' or instance.id == 'i-036c5c38ccf4ad90b' or instance.id == 'i-0dd8069a3598ec8a5'):
					if instance.state['Name'] == 'running':
						#print("I will destroy")
						worker_destroy-=1
						ec2_destroy(instance.id)
				

		time.sleep(30)



if __name__ == "__main__":
	auto()
