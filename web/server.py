# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#FLASK_APP=server.py flask run
from flask_socketio import SocketIO
from flask import render_template
from init import app,socketio
import commands

import pid

@app.route('/')
def index():
    return open('static/index.html').read()
    #return "Hello, World!"

if __name__ == '__main__':
    #app.run(host='127.0.0.1', debug=True)
    socketio = SocketIO(app,host='192.168.8.162', debug=True)
