#!./flask/bin/python
from app import webapp
webapp.run(host='0.0.0.0',debug=True,threaded=True)
#webapp.run(host='0.0.0.0')
