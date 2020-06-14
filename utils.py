import struct
import redis
import numpy as np
import math

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)


def save_bytes_to_redis(r, encoded, name):
    """Store given image encoded in bytes in redis"""
    r.set(name, encoded)
    return


def load_bytes_from_redis(r, name):
    """Retrieve image encoded in bytes from Redis key"""
    encoded = r.get(name)
    return encoded


def save_numpy_to_redis(r, array, name):
    """Store given Numpy array in Redis under key name"""
    encoded = array.tobytes()
    r.set(name, encoded)  # Store encoded data in Redis
    return


def load_numpy_from_redis(r, name, dtype=np.uint8):
    """Retrieve Numpy array from Redis key name"""
    encoded = r.get(name)
    hwc_offset = 4*3
    h, w, c = struct.unpack('>III', encoded[:hwc_offset])
    array = np.frombuffer(encoded, dtype=dtype, offset=hwc_offset).reshape(h, w, c)
    return array


def stack_frames(frames):
    """Convert to gray frame and create stack"""
    assert len(frames) == 5
    gray_frames = [frame[:, :, 0] for frame in frames]
    frame = np.dstack(gray_frames)
    return frame


def find_center(box1, box2):
    """Find center point of box"""
    return [(box1[0]+box2[0])/2, (box1[1]+box2[1])/2]


def extrapolation_box(first_boxes, first_timestamp, second_boxes, second_timestamp, third_timestamp):
    """Extrapolation box by timestamp"""
    if first_boxes is None or second_boxes is None:
            return []
    # find center point of first box
    first_center = find_center([first_boxes[0][0], first_boxes[0][1]], [first_boxes[0][2], first_boxes[0][3]])
    # find center point of second box
    second_center = find_center([second_boxes[0][0], second_boxes[0][1]], [second_boxes[0][2], second_boxes[0][3]])
    # find ratio: A, B, C => CA/BA
    k = (third_timestamp - first_timestamp)/(second_timestamp - first_timestamp)
    # find vector CA
    vector13 = [(second_center[0] - first_center[0])*k, (second_center[1] - first_center[1])*k]
    # find center point of new box: vectorCA + first_box
    third_center = [vector13[0] + first_center[0], vector13[1] + first_center[1]]

    corner = [second_boxes[0][2], second_boxes[0][1]]   # Find top_right point of second_box
    length = corner[0] - second_boxes[0][0]             # Length of second_box
    width = second_boxes[0][3] - corner[1]              # Width of second_box
    # find new box after extrapolation
    third_boxes = [[third_center[0]-length, third_center[1]-width, third_center[0]+length, third_center[1]+width]]
    return third_boxes
