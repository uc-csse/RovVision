# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import sys
sys.path.append('..')

app = Flask(__name__)
socketio = SocketIO(app)
