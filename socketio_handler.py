import paho.mqtt.client as mqtt
import socketio
from engineio.payload import Payload
from flask_socketio import SocketIO, emit
from socketio.exceptions import BadNamespaceError

from enumss import BROKER_HOST, BROKER_PORT, UPDATE_FRAME_TOPIC_BROKER, \
                   UPDATE_STACK_TOPIC_BROKER, UPDATE_BOXES_TOPIC_BROKER

# standard Python
sio = socketio.Client()
sio.connect('http://localhost:4321', namespaces=["/test"])
print('my sid is', sio.sid)
Payload.max_decode_packets = 500


def send_frame(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the 'update/frame' Topic  """
    try:
        sio.emit('new_frame_event', {'data': msg.payload, 'room': ""}, namespace="/test")
        print("send frame")
    except BadNamespaceError:
        print("emit error, wait to emit again")
    except:
        print("emit error")


def send_boxes(client, userdata, msg):
    """ The callback for when a PUBLISH message is received from the 'update/boxes' Topic  """
    print("send boxes")
    try:
        sio.emit("new_boxes_event", {'data': msg.payload, 'room': ""}, namespace="/test")
    except BadNamespaceError:
        print("emit error, wait to emit again")
    except:
        print("emit error")


client = mqtt.Client("socketio_handler")                            # Create instance of client with client ID ...
client.connect(BROKER_HOST, BROKER_PORT)                            # Connect to broker
client.subscribe(UPDATE_FRAME_TOPIC_BROKER)                         # Subscribe to "update/frame" topic
client.message_callback_add(UPDATE_FRAME_TOPIC_BROKER, send_frame)  # Callback to send_frame method
client.subscribe(UPDATE_BOXES_TOPIC_BROKER)                         # Subscribe to "update/boxes" topic
client.message_callback_add(UPDATE_BOXES_TOPIC_BROKER, send_boxes)  # Callback to send_boxes method
client.loop_forever()                                               # Start networking daemon
