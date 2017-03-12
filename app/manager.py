from flask import render_template, redirect, url_for, request
from app import webapp
import boto3
from app.config import db_config
from datetime import datetime, timedelta
from operator import itemgetter


@webapp.route('/manager',methods=['GET'])
#Display details about a specific instance.
def ec2_view():
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.all()

    cpu_stats_list = []

    for instance in instances:
        id = instance.id

        client = boto3.client('cloudwatch')

        metric_name = 'CPUUtilization'

        ##    CPUUtilization, NetworkIn, NetworkOut, NetworkPacketsIn,
        #    NetworkPacketsOut, DiskWriteBytes, DiskReadBytes, DiskWriteOps,
        #    DiskReadOps, CPUCreditBalance, CPUCreditUsage, StatusCheckFailed,
        #    StatusCheckFailed_Instance, StatusCheckFailed_System


        namespace = 'AWS/EC2'
        statistic = 'Average'                   # could be Sum,Maximum,Minimum,SampleCount,Average

        cpu = client.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=60 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName=metric_name,
            Namespace=namespace,  # Unit='Percent',
            Statistics=[statistic],
            Dimensions=[{'Name': 'InstanceId', 'Value': id}]
        )

        cpu_stats = []

        for point in cpu['Datapoints']:
            hour = point['Timestamp'].hour
            minute = point['Timestamp'].minute
            time = hour + minute/60
            cpu_stats.append([time,point['Average']])

        cpu_stats = sorted(cpu_stats, key=itemgetter(0))

        cpu_stats_list.append(cpu_stats)

    return render_template("view.html",title="Instance Info",
                           cpu_stats_list=cpu_stats_list,
                           instances=instances)


@webapp.route('/manager/grow',methods=['POST'])
def ec2_grow_ratio():
    print("grow")
    return redirect(url_for('ec2_view'))

@webapp.route('/manager/shrink',methods=['POST'])
def ec2_shrink_ratio():
    print("shrink")
    return redirect(url_for('ec2_view'))

@webapp.route('/manager/Gthreshold',methods=['POST'])
def ec2_grow_threshold():
    return redirect(url_for('ec2_view'))

@webapp.route('/manager/Sthreshold',methods=['POST'])
def ec2_shrink_threshold():
    return redirect(url_for('ec2_view'))

@webapp.route('/manager/create',methods=['POST'])
# Start a new EC2 instance
def ec2_create():

    ec2 = boto3.resource('ec2')

    ec2.create_instances(
            ImageId=db_config['ami_id'], 
            MinCount=1, 
            MaxCount=1,
            KeyName='1779_key',
            SecurityGroupIds=['sg-95976cea',],
            InstanceType='t2.small',
            Monitoring={'Enabled': True}
            )

    return redirect(url_for('ec2_view'))



@webapp.route('/manager/delete/<id>',methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_view'))
