from flask import Blueprint, request
import cv2
import redis
import threading
import subprocess
from subprocess import Popen, PIPE
from utils import r
from enumss import RTSP_LINK_KEY_REDIS

api = Blueprint('stream', __name__)
redisClient = redis.StrictRedis(host='localhost', port=6379, db=0)
RUN_RTSP_DAEMON_PROCESS = None


def run_rtsp_daemon():
    global RUN_RTSP_DAEMON_PROCESS
    RUN_RTSP_DAEMON_PROCESS = Popen(['python', 'rtsp_daemon.py'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = RUN_RTSP_DAEMON_PROCESS.communicate()


@api.route('/connect', methods=['GET'])
def check_connect():
    global RUN_RTSP_DAEMON_PROCESS
    response_fail = {
        'status': False,
        'msg': "Connect to rtsp link fail"
    }
    response_true = {
        'status': True,
        'msg': "Connect to rtsp link successfully"
    }
    params = {
        "rtsp_link": request.args.get('rtsp_link'),
        "username": request.args.get('username'),
        "password": request.args.get('password')
    }
    # At least one process is running
    if RUN_RTSP_DAEMON_PROCESS is not None:
        return response_fail, 400
    # Get rtsp_link from input with some case
    if params["rtsp_link"].find("rtsp") == 0:
        if params["username"] == "" and params['password'] == "":
            rtsp_link = params["rtsp_link"]
        else:
            if params["rtsp_link"].find("@") > 0 and params["rtsp_link"].find(":") > 0:
                rtsp_link = params["rtsp_link"]
            else:
                rtsp_link = "rtsp://" + params["username"] + ":" + params["password"] + "@" + \
                        params["rtsp_link"][7:len(params["rtsp_link"])]
    else:
        rtsp_link = params["rtsp_link"]
    try:
        # Check rtsp_link
        check = cv2.VideoCapture(rtsp_link).isOpened()
    except:
        return response_fail, 400
    if check is True:
        r.set(RTSP_LINK_KEY_REDIS, rtsp_link)                       # Save rtsp_link to redis
        t1 = threading.Thread(target=run_rtsp_daemon, daemon=True)  # Create thread to run rtsp_daemon
        t1.start()                                                  # Start thread
        return response_true, 200
    return response_fail, 400


@api.route('/disconnect', methods=['GET'])
def disconnect():
    global RUN_RTSP_DAEMON_PROCESS
    response_fail = {
        'status': False,
        'msg': "Disconnect rtsp link fail"
    }
    response_true = {
        'status': True,
        'msg': "Disconnect rtsp link successfully"
    }
    if RUN_RTSP_DAEMON_PROCESS is None:
        return response_fail, 400
    params = {
        "rtsp_link": request.args.get('rtsp_link'),
        "username": request.args.get('username'),
        "password": request.args.get('password')
    }
    # Get rtsp_link from input with some case
    if params["rtsp_link"].find("rtsp") == 0:
        if params["username"] == "" and params['password'] == "":
            rtsp_link = params["rtsp_link"]
        else:
            if params["rtsp_link"].find("@") > 0 and params["rtsp_link"].find(":") > 0:
                rtsp_link = params["rtsp_link"]
            else:
                rtsp_link = "rtsp://" + params["username"] + ":" + params["password"] + "@" + \
                            params["rtsp_link"][7:len(params["rtsp_link"])]
    else:
        rtsp_link = params["rtsp_link"]
    if cv2.VideoCapture(rtsp_link).isOpened():
        if RUN_RTSP_DAEMON_PROCESS is not None:
            subprocess.Popen.kill(RUN_RTSP_DAEMON_PROCESS)
            RUN_RTSP_DAEMON_PROCESS = None
            return response_true, 200
    return response_fail, 400
