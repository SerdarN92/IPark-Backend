#! /usr/bin/python3

#! /usr/bin/env PYTHONPATH=/home/student/Desktop/IPark-Backend/ipark python3
import sys
sys.path.insert(0, '/home/student/Desktop/IPark-Backend/ipark')

from ipark.frontend.APIFrontend import app

#from flup.server.fcgi import WSGIServer
from flipflop import WSGIServer

#if __name__ == '__main__':
WSGIServer(app).run()
# WSGIServer(app, bindAddress='/tmp/ipark-fcgi.sock').run()
