#!/usr/bin/python

import time
import boto3
import mysql.connector
from app.config import db_config


def connect_to_database():
	return mysql.connector.connect(user=db_config['user'], 
	                               password=db_config['password'],
	                               host=db_config['host'],
	                               database=db_config['cloudWatch'])


def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = connect_to_database()
	return db


def teardown_db(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

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

	instances = ec2.instances.all()
	
	value = 'ece1779worker'

	tag = instance.create_tags(
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
	            'InstanceId': instance.id
	        },
	    ]
	)

def auto():
	cnx = get_db()
	cursor = cnx.cursor()

	query = "SELECT * FROM workers WHERE id = %s"

	cursor.execute(query,(1,))

	row = cursor.fetchone()

	grow_ratio = row[1]
	shrink_ratio = row[2]
	grow_threshold = row[3]
	shrink_threshold = row[4]

	client = boto3.client('cloudwatch')

	metric_name = 'CPUUtilization'

	namespace = 'AWS/EC2'
	statistic = 'Maximum'                   

	cpu = client.get_metric_statistics(
	    Period=1 * 60,
	    StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
	    EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
	    MetricName=metric_name,
	    Namespace=namespace,  # Unit='Percent',
	    Statistics=[statistic],
	    Dimensions=[{'Name': 'InstanceId', 'Value': id}]
	)

	cpu_stats = []

	for point in cpu['Datapoints']:
		print(point['Maximum'])
		cpu_stats.append(point['Maximum'])

	if max(cpu_stats) > grow_threshold:
		for i in range(grow_ratio)
		ec2_create()
	elif min(cpu_stats) < shrink_threshold:

        



if __name__ == "__main__":
	auto()
