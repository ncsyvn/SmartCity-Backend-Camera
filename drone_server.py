from threading import Lock
from flask import Flask,  session, request
from flask_socketio import SocketIO, emit
from enumss import HOST, PORT
from utils import load_bytes_from_redis, r, extrapolation_box
from engineio.payload import Payload
from api import api
from flask_cors import CORS
import datetime
import random
import json

Payload.max_decode_packets = 500
async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")
CORS(app)
thread = None
thread_lock = Lock()

FIRST_TIMESTAMP = None   # Global variable contain timestamp of box1
SECOND_TIMESTAMP = None  # Global variable contain timestamp of box2
FIRST_BOXES = None       # Global variable contain box1
SECOND_BOXES = None      # Global variable contain box2


@socketio.on('new_frame_event', namespace='/test')
def send_new_frame(message):
    global FIRST_TIMESTAMP
    global SECOND_TIMESTAMP
    global FIRST_BOXES
    global SECOND_BOXES
    session['receive_count'] = session.get('receive_count', 0) + 1
    room = message['room']
    frame_name = message['data']
    image_data = load_bytes_from_redis(r, frame_name)  # Load image from redis
    time_now = datetime.datetime.now().timestamp()     # Get current time

    """Extrapolation box"""
    third_boxes = extrapolation_box(FIRST_BOXES, FIRST_TIMESTAMP, SECOND_BOXES, SECOND_TIMESTAMP, time_now)
    if room:
        # transfer size is smallest
        emit('imageConversionByClient', {
            'buffer': image_data,
            'timestamp': time_now,
            'boxes': third_boxes,
            'scores': [0]
        }, room=room)
    else:
        # transfer size is smallest
        emit('imageConversionByClient', {
            'buffer': image_data,
            'timestamp': time_now,
            'boxes': third_boxes,
            'scores': [0]
        }, broadcast=True)


@socketio.on('new_boxes_event', namespace='/test')
def send_new_boxes(message):
    global FIRST_BOXES
    global SECOND_BOXES
    global FIRST_TIMESTAMP
    global SECOND_TIMESTAMP
    session['receive_count'] = session.get('receive_count', 0) + 1
    room = message['room']
    boxes_name = message['data']
    boxes_data = load_bytes_from_redis(r, boxes_name)  # Load box from redis
    boxes_data = boxes_data.decode('utf8')             # Convert to string
    boxes_data = json.loads(boxes_data)                # Convert to json
    boxes = boxes_data["bbox"]                         # Get list boxes from json
    if len(boxes) == 0:                                # If boxes is None: pass
        FIRST_BOXES = None
    else:
        # Swap 2 box, update last box
        FIRST_BOXES = SECOND_BOXES
        SECOND_BOXES = boxes
        FIRST_TIMESTAMP = SECOND_TIMESTAMP
        SECOND_TIMESTAMP = datetime.datetime.now().timestamp()
    # if room:
    #     emit('boxesConversionByClient', {'buffer': boxes_data}, room=room)       # transfer size is smallest
    # else:
    #     emit('boxesConversionByClient', {'buffer': boxes_data}, broadcast=True)  # transfer size is smallest
    # print("Box data is : ", boxes_data['bbox'])


@socketio.on('connect', namespace='/test')
def connect():
    print('Client connected', request.sid)


@socketio.on('disconnect', namespace='/test')
def disconnect():
    print('Client disconnected', request.sid)


def register_blueprints(app):
    """
    Init blueprint for api url
    :param app:
    :return:
    """
    app.register_blueprint(api, url_prefix='/api/v1/stream')


register_blueprints(app)
if __name__ == '__main__':
    socketio.run(app, debug=True, host=HOST, port=PORT)
