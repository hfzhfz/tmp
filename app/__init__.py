import os
from flask import Flask, session

webapp = Flask(__name__)

webapp.secret_key = os.urandom(24)

from app import image
from app import main
from app import manager

