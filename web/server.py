# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#FLASK_APP=test_cam.py flask run
from flask_socketio import SocketIO
from init import app,socketio
import commands

import pid

@app.route('/')
def index():
    #return render_template('index.html')
    return "Hello, World!"

if __name__ == '__main__':
    #app.run(host='127.0.0.1', debug=True)
    socketio = SocketIO(app,host='127.0.0.1', debug=True)
