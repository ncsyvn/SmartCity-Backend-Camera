import paho.mqtt.client as mqttClient
import time
import cv2
import random
from utils import save_bytes_to_redis, save_numpy_to_redis, stack_frames, r
from enumss import FRAME_WIDTH, FRAME_HEIGHT, BROKER_HOST, \
    BROKER_PORT, UPDATE_FRAME_TOPIC_BROKER, UPDATE_STACK_TOPIC_BROKER,\
    LEN_LIST_FRAME, STACK_KEY_REDIS, FRAME_KEY_REDIS, \
    RTSP_LINK_KEY_REDIS, FRAME_SEND_INDEX, DISTANCE_FRAME

rtsp_link = r.get(RTSP_LINK_KEY_REDIS).decode("utf-8")
PUBSUB_CONNECTED = False   # global variable for the state of the connection


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global PUBSUB_CONNECTED  # Use global variable
        PUBSUB_CONNECTED = True  # Signal connection
    else:
        print("Connection failed")


pubsub_client = mqttClient.Client("rtsp_daemon")  # create new instance
pubsub_client.on_connect = on_connect  # attach function to callback
pubsub_client.connect(BROKER_HOST, BROKER_PORT)  # connect to broker
pubsub_client.loop_start()

while not PUBSUB_CONNECTED:    # Wait for connection
    time.sleep(0.1)

if __name__ == '__main__':
    print("Start rtsp daemon")
    try:
        list_frames = []
        vcap = cv2.VideoCapture(rtsp_link)
        while True:
            # Read frame
            success, frame = vcap.read()
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
            # Case 1: Enough DISTANCE_FRAME*2+1 frame to create good stack with 5 frame
            if len(list_frames) == LEN_LIST_FRAME:
                list_frames.pop(0)
                list_frames.append(frame)
                # Stack and store new stack
                # TODO: stack frame here
                index = DISTANCE_FRAME * 2 + 1
                stacked_frame = stack_frames([list_frames[LEN_LIST_FRAME - index],
                                             list_frames[LEN_LIST_FRAME - index + DISTANCE_FRAME - 1],
                                             list_frames[LEN_LIST_FRAME - index + DISTANCE_FRAME],
                                             list_frames[LEN_LIST_FRAME - index + DISTANCE_FRAME + 1],
                                             list_frames[LEN_LIST_FRAME-1]])
                encoded = cv2.imencode('.jpg', list_frames[FRAME_SEND_INDEX])[1]   # Encode image
            # Case 2: Not enough DISTANCE_FRAME*2+1 frame, create stack with 5 same frame
            else:
                list_frames.append(frame)
                stacked_frame = stack_frames([frame, frame, frame, frame, frame])
                encoded = cv2.imencode('.jpg', frame)[1]                 # Encode image and store new frame to redis
            image_data = encoded.tostring()                                    # Convert to string
            save_numpy_to_redis(r, stacked_frame, STACK_KEY_REDIS)             # Save stack to redis
            save_bytes_to_redis(r, image_data, FRAME_KEY_REDIS)                # Store new frame to redis
            pubsub_client.publish(UPDATE_STACK_TOPIC_BROKER, STACK_KEY_REDIS)  # Publish new stack
            pubsub_client.publish(UPDATE_FRAME_TOPIC_BROKER, FRAME_KEY_REDIS)  # Publish new frame
            print("publish successfully")
    except cv2.error:
        print("error")
    except KeyboardInterrupt:
        print("Disconnect PubSub")
        pubsub_client.disconnect()
        pubsub_client.loop_stop()


