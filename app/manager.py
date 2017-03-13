from flask import render_template, redirect, url_for, request, g, session
from app import webapp
import boto3
import mysql.connector
from app.config import db_config
from datetime import datetime, timedelta
from operator import itemgetter

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


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/manager',methods=['GET'])
#Display details about a specific instance.
def ec2_view():
    if 'username' in session:
        username = session['username']
    else:
        return render_template("login.html")

    ec2 = boto3.resource('ec2')

    instances = ec2.instances.all()

    cpu_stats_list = []
    option = []
    client = boto3.client('cloudwatch')

    for instance in instances:
        id = instance.id

        metric_name = 'CPUUtilization'


        namespace = 'AWS/EC2'
        statistic = 'Average'                   

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



    cnx = get_db()
    cursor = cnx.cursor()

    query = "SELECT * FROM workers WHERE id = %s"

    cursor.execute(query,(1,))

    row = cursor.fetchone()

    if row is None:
        query = ''' INSERT INTO workers (id, grow_ratio, shrink_ratio, grow_threshold, shrink_threshold)
                       VALUES (%s, %s, %s, %s, %s)
        '''

        cursor.execute(query,(1,2,2,30,20))
        cnx.commit()

    else:
        option.append(row[1])
        option.append(row[2])
        option.append(row[3])
        option.append(row[4])

    return render_template("view.html",title="Instance Info",
                                       cpu_stats_list=cpu_stats_list,
                                       instances=instances,
                                       option=option)


@webapp.route('/manager/grow',methods=['POST'])
def ec2_grow_ratio():
    print("Gratio")

    ratio = request.form.get('Gratio')

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' UPDATE workers SET grow_ratio = %s
    '''
    cursor.execute(query,(ratio))
    cnx.commit()

    #return redirect(url_for('ec2_view'))
    return None

@webapp.route('/manager/shrink',methods=['POST'])
def ec2_shrink_ratio():
    print("Sratio")

    ratio = request.form.get('Sratio')

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' UPDATE workers SET shrink_ratio = %s
    '''
    cursor.execute(query,(ratio))
    cnx.commit()

    #return redirect(url_for('ec2_view'))
    return None

@webapp.route('/manager/Gthreshold',methods=['POST'])
def ec2_grow_threshold():
    print("Gthreshold")

    threshold = request.form.get('grow')

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' UPDATE workers SET grow_threshold = %s
    '''
    cursor.execute(query,(ratio))
    cnx.commit()

    #return redirect(url_for('ec2_view'))
    return None

@webapp.route('/manager/Sthreshold',methods=['POST'])
def ec2_shrink_threshold():
    print("Sthreshold")

    threshold = request.form.get('shrink')

    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' UPDATE workers SET shrink_threshold = %s
    '''
    cursor.execute(query,(ratio))
    cnx.commit()

    #return redirect(url_for('ec2_view'))
    return None

@webapp.route('/manager/create',methods=['POST'])
# Start a new EC2 instance
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
    number = len(instances) - 2
    value = 'ece1779worker' + str(number)
    
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
    return redirect(url_for('ec2_view'))



@webapp.route('/manager/delete/<id>',methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_view'))