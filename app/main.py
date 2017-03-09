from flask import render_template, redirect, url_for, request, g, session
from app import webapp
import mysql.connector
from app.config import db_config
import random
import bcrypt


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


@webapp.route('/index',methods=['GET'])
@webapp.route('/main',methods=['GET'])
# Display an HTML page with links
def main():
    return render_template("main.html",title="Web & Image")

@webapp.route('/login',methods=['POST'])
def login():
	userName = request.form.get('userName',"")
	password = request.form.get('password',"")

	if userName == "" or password == "":
		error_msg="Error: All fields are required!"
		return render_template("login.html", login_msg = error_msg)

	cnx = get_db()
	cursor = cnx.cursor()

	query = "SELECT * FROM users WHERE username = %s"

	cursor.execute(query,(userName,))

	row = cursor.fetchone()

	if row is None:
		error_msg="User not exist!"
		return render_template("login.html", login_msg = error_msg)

	hashed = row[3]
	
	if hashed.encode('utf8') == bcrypt.hashpw(password.encode('utf8'),hashed.encode('utf8')):
		session['username'] = userName
		return render_template("/main.html", title="Web & Image")
	else:
		error_msg="Incorrect Password!"
		return render_template("login.html", login_msg = error_msg)



@webapp.route('/signup',methods=['POST'])
def signup():
	userName = request.form.get('userName',"")
	password = request.form.get('password',"")

	if userName == "" or password == "":
		error_msg="Error: All fields are required!"
		return render_template("login.html", signup_msg = error_msg)

	cnx = get_db()
	cursor = cnx.cursor()

	query = "SELECT * FROM users WHERE username = %s"

	cursor.execute(query,(userName,))

	row = cursor.fetchone()

	if not row is None:
		error_msg="user exist! pick another one"
		return render_template("login.html", signup_msg = error_msg)

	salt = bcrypt.gensalt()
	hashed = bcrypt.hashpw(password.encode('utf8'), salt)
	query = ''' INSERT INTO users (username, salt, password)
		               VALUES (%s, %s, %s)'''
	
	cursor.execute(query,(userName,salt.decode('utf-8'),hashed.decode('utf-8')))
	cnx.commit()
	session['username'] = userName
	return render_template("/main.html", title="Web & Image")


@webapp.route('/',methods=['GET'])
def welcome_page():
	return render_template("login.html")




