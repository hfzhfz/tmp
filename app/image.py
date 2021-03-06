import os
from flask import render_template, redirect, url_for, request, g, session
from werkzeug.utils import secure_filename
from app import webapp
import mysql.connector
from app.config import db_config
from wand.image import Image
from wand.display import display
import boto3
import bcrypt


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'], 
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@webapp.route('/images/create',methods=['POST'])
def images_create_save():
	if 'username' in session:
		username = session['username']
	else:
		return render_template("login.html")

	
	s3 = boto3.resource('s3')

	if 'file' not in request.files:
		msg = "no file"
		return render_template("/main.html", msg = msg, title="Web & Image")

	file = request.files['file']
    
	if file.filename == '':
		msg = "empty"
		return render_template("/main.html", msg = msg, title="Web & Image")

	if file and allowed_file(file.filename):

		filename = secure_filename(file.filename)
		path = db_config['path'] + '/'

		cnx = get_db()
		cursor = cnx.cursor()

		query = "SELECT * FROM images WHERE key1 = %s"
		cursor.execute(query,(filename,))
		row = cursor.fetchone()
		if not row is None:
			msg = "file exists! try another one"
			return render_template("/main.html", msg = msg, title="Web & Image")

		
		file.save(os.path.join(path, filename))

		fname = file.filename.rsplit('.', 1)[0]
		ext = file.filename.rsplit('.', 1)[1]
		path_name = path + filename

		key1 = username  + "_" + fname + "_origin." + ext
		key2 = username  + "_" + fname + "_flopped." + ext
		key3 = username  + "_" + fname + "_resized." + ext
		key4 = username  + "_" + fname + "_color." + ext

		data = open(path_name, 'rb')
		#f=open(path_name,'rb')
		#s3.upload_fileobj(f, 'lizw-a1', key1)
		s3.Bucket('lizw-a1').put_object(Key=key1, Body=data)

		with Image(filename = path_name) as image:
			with image.clone() as flopped:
				flopped.flop()
				new_file = path + username  + "_" + fname + "_flopped." + ext
				flopped.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key2, Body=data)
				os.remove(new_file)

			with image.clone() as resize:
				resize.resize(180, 180)
				new_file = path + username  + "_" + fname + "_resized." + ext
				resize.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key3, Body=data)
				os.remove(new_file)

			with image.clone() as color:
				frequency = 3
				phase_shift = -90
				amplitude = 0.2
				bias = 0.7
				color.function('sinusoid', [frequency, phase_shift, amplitude, bias])
				new_file = path + username  + "_" + fname + "_color." + ext
				color.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key4, Body=data)
				os.remove(new_file)
		
		os.remove(path_name)

		query = "SELECT * FROM users WHERE username = %s"
		cursor.execute(query,(username,))
		row = cursor.fetchone()
		userId = row[0]
		

		query = ''' INSERT INTO images (userId, key1, key2, key3, key4)
		               VALUES (%s, %s, %s, %s, %s)
		'''

		cursor.execute(query,(userId,key1,key2,key3,key4))
		cnx.commit()

		msg = "success"

	
	return render_template("/main.html", msg = msg, title="Web & Image")



@webapp.route('/gallery',methods=['POST'])
def gallery():
	if 'username' in session:
		username = session['username']

		s3 = boto3.client('s3')

		cnx = get_db()
		cursor = cnx.cursor()

		query = "SELECT * FROM users WHERE username = %s"
		cursor.execute(query,(username,))
		row = cursor.fetchone()
		userId = row[0]

		session['userId'] = userId

		query = "SELECT * FROM images WHERE userId = %s"
		cursor.execute(query,(userId,))


		path_list = []
		id_list = []
		
		for row in cursor:

			url = s3.generate_presigned_url(
				ClientMethod='get_object',
				Params={
					'Bucket': 'lizw-a1',
					'Key': row[4]
				}
			)
			id_list.append(row[4]) 
			path_list.append(url)
			

		return render_template("gallery.html", path_list = path_list, id_list = id_list, username=username)
	else:
		return render_template("login.html")
    
    
@webapp.route('/transformed',methods=['GET'])
def transformed():
	if 'username' in session:
		username = session['username']
		image_id = request.args.get('id')
		
		s3 = boto3.client('s3')
		cnx = get_db()
		cursor = cnx.cursor()

		query = "SELECT * FROM images WHERE key3 = %s"
		cursor.execute(query,(image_id,))

		path_list = []
		row = cursor.fetchone()

		if row is None:
			msg = "image not exist"
			return render_template("gallery.html", msg = msg, username=username)

		for i in range(2,6):
			url = s3.generate_presigned_url(
				ClientMethod='get_object',
				Params={
					'Bucket': 'lizw-a1',
					'Key': row[i]
				}
			)
			path_list.append(url)


		return render_template("transformed.html", path_list = path_list, username=username)

	else:
		return render_template("login.html")
	


@webapp.route('/test/FileUpload',methods=['POST'])
def file_upload_test():
	
	userName = request.form.get('userID',"")
	password = request.form.get('password',"")

	if userName == "" or password == "":
		error_msg="Error: All fields are required!"
		return redirect(url_for('test_page'))

	cnx = get_db()
	cursor = cnx.cursor()

	query = "SELECT * FROM users WHERE username = %s"

	cursor.execute(query,(userName,))

	row = cursor.fetchone()

	if row is None:
		error_msg="User not exist!"
		return redirect(url_for('test_page'))

	userId = row[0]
	hashed = row[3]
	
	if not (hashed.encode('utf8') == bcrypt.hashpw(password.encode('utf8'),hashed.encode('utf8'))):
		
		error_msg="Incorrect Password!"
		return redirect(url_for('test_page'))

	session['username'] = userName
	username = userName

	s3 = boto3.resource('s3')

	if 'uploadedfile' not in request.files:
		msg = "no file"
		return redirect(url_for('test_page'))

	file = request.files['uploadedfile']
    
	if file.filename == '':
		msg = "empty"
		return redirect(url_for('test_page'))

	if file and allowed_file(file.filename):

		filename = secure_filename(file.filename)
		path = db_config['path'] + '/'

		query = "SELECT * FROM images WHERE key1 = %s"
		cursor.execute(query,(filename,))
		row = cursor.fetchone()
		if not row is None:
			msg = "file exists! try another one"
			return redirect(url_for('test_page'))

		
		file.save(os.path.join(path, filename))

		fname = file.filename.rsplit('.', 1)[0]
		ext = file.filename.rsplit('.', 1)[1]
		path_name = path + filename

		key1 = username  + "_" + fname + "_origin." + ext
		key2 = username  + "_" + fname + "_flopped." + ext
		key3 = username  + "_" + fname + "_resized." + ext
		key4 = username  + "_" + fname + "_color." + ext

		data = open(path_name, 'rb')
		#f=open(path_name,'rb')
		#s3.upload_fileobj(f, 'lizw-a1', key1)
		s3.Bucket('lizw-a1').put_object(Key=key1, Body=data)

		with Image(filename = path_name) as image:
			with image.clone() as flopped:
				flopped.flop()
				new_file = path + username  + "_" + fname + "_flopped." + ext
				flopped.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key2, Body=data)
				os.remove(new_file)

			with image.clone() as resize:
				resize.resize(180, 180)
				new_file = path + username  + "_" + fname + "_resized." + ext
				resize.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key3, Body=data)
				os.remove(new_file)

			with image.clone() as color:
				frequency = 3
				phase_shift = -90
				amplitude = 0.2
				bias = 0.7
				color.function('sinusoid', [frequency, phase_shift, amplitude, bias])
				new_file = path + username  + "_" + fname + "_color." + ext
				color.save(filename = new_file)
				data = open(new_file, 'rb')
				s3.Bucket('lizw-a1').put_object(Key=key4, Body=data)
				os.remove(new_file)
		
		os.remove(path_name)


		query = ''' INSERT INTO images (userId, key1, key2, key3, key4)
		               VALUES (%s, %s, %s, %s, %s)
		'''

		cursor.execute(query,(userId,key1,key2,key3,key4))
		cnx.commit()

		msg = "success"

	
	return redirect(url_for('test_page'))


@webapp.route('/test_page',methods=['GET'])
def test_page():
	return render_template("test.html")

