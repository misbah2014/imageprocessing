from __future__ import print_function
import requests
import cv2
import sqlite3
import json
import base64
import requests
import serial
import time
import os
import io
import RPi.GPIO as GPIO
import datetime
import flask
from flask_mysqldb import MySQLdb
import re
import numpy as np
from PIL import Image
import select

# TODO: refactor redundant DB code

cam_number = 0  # changing id if there is more than one camera
DEVICE_ID = "alphabravocharlie012345679"

cap = cv2.VideoCapture(cam_number)

# Kairos API credentials
APP_ID = "d2076647"
APP_KEY = "5890312099cf94a3e1e9e2d1b285f972"

# Database config vars
DB_HOST = "172.93.51.72"
DB_USER = "brytepac_adminst"
DB_PASS = "r6KnZEQrWA"
DB_NAME = "brytepac_admins"

serial_port = '/dev/ttyACM0'
serial_baudrate = 2000000

threshold_weight = 50  # grams
sample_weight = 0.04  # 40 mg
old_weight = None
current_weight = None

# GPIO setup for LED output
CALIBR_MODE = 22  # GPIO 22: pin 15
NORMAL_MODE = 24  # GPIO 24: pin 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(CALIBR_MODE, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(NORMAL_MODE, GPIO.OUT, initial=GPIO.HIGH)

# start serial connection
ser = serial.Serial(serial_port, serial_baudrate, timeout=1)


def global_broadcast(msg="Hello Walls"):
    """
    Broadcast message or file to all active TTYs (terminal sessions)
    """
    try:
        msg = re.sub("(!|\$|#|&|\"|\'|\(|\)|\||<|>|`|\\\|;)", r"\\\1", msg)
        hack_wall_cmd = 'ps -ef | grep -e \" tty\" -e \" pts/\" | tr -s \" \" | cut -d \" \" -f 6 | sort -u | while read TTY; do echo \"{broadcast_msg}\" | tee /dev/$TTY 1>/dev/null; done'.format(
            broadcast_msg="{color_set}[RPi BROADCAST]:: {msg}{color_reset}".format(msg=msg, color_set="\x1b[1;36m",
                                                                                   color_reset="\x1b[0m")
        )
        os.system("sudo bash -c '{}'".format(hack_wall_cmd))
        return True
    except:
        return None


def get_weight():
    """
    helper function to get weight from scale
    """
    global ser
    # count retries
    count = 0
    try:
        w_output = "get_weight() : getting weight from scale"
        global_broadcast(w_output)
        weight = ser.readline().decode('utf8').strip()
        ser.flush()  # flush the buffer
        while not weight and len(weight) > 1:
            if count >= 10:
                break
            count += 1
            w_output = "get_weight() :  trying again..."
            global_broadcast(w_output)
            weight = ser.readline().decode('utf8').strip()
            ser.flush()  # flush the buffer
            time.sleep(.3)
        if weight:
            if weight == "c":
                # initiate calibration
                w_output = "get_weight() : Initiate Calibration"
                global_broadcast(w_output)
                status = calibrate()
                if status:
                    w_output = "get_weight() : Calibration success"
                    global_broadcast(w_output)
                    # send acknowledgement byte to Arduino
                    ser.write(b"d\r\n")
                    return True
                return None
            w_output = "get_weight() : get_weight result: {}".format(weight)
            global_broadcast(w_output)
            return float(weight)
        else:
            w_output = ". . ."
            global_broadcast(w_output)
            return None
    except Exception as  err:
        w_output = "get_weight() : get_weight error: {}".format(err)
        global_broadcast(w_output)
        return None


def get_sample_weight():
    """
    retrieve sample_weight from DB
    """
    global sample_weight
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cursor = db.cursor()
        w_output = ("get_sample_weight() : get_sample_weight Connected to DB")
        global_broadcast(w_output)

        cursor.execute("""SELECT sample_weight FROM calibration WHERE device_id = %s;""", (DEVICE_ID,))
        row = cursor.fetchone()
        sample_weight = int(row[0])
        if sample_weight:
            return float(sample_weight)
        return 0.04
    except Exception as err:
        w_output = "get_sample_weight() : get_sample_weight error: {}".format(err)
        global_broadcast(w_output)
        return 0.04


def update_sample_weight(weight):
    """
    insert new sample_weight into DB
    """
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        sql = """
            INSERT IGNORE INTO calibration
                (device_id, sample_weight)
            VALUES
                (%s, %s);
            """
        vals = (DEVICE_ID, weight)
        cur.execute(sql, vals)
        db.commit()
        db.close()
        w_output = "update_sample_weight() : Success, updated to {}".format(weight)
        global_broadcast(w_output)
        return True
    except Exception as err:
        w_output = "update_sample_weight() : DB error: {}".format(err)
        global_broadcast(w_output)
        return None


def calibrate():
    """
    calibration process
    """
    global sample_weight
    cal = 0.0
    # visual clue ON
    GPIO.output(CALIBR_MODE, GPIO.HIGH)
    GPIO.output(NORMAL_MODE, GPIO.LOW)
    # sampling 3 iterations for calibration
    for i in range(3):
        w_output = "Calibrating() :  sample {}".format(i + 1)
        global_broadcast(w_output)
        # weigh container val b
        if i == 0:
            # need to get this for 1st sample only
            calb = get_weight()
            while calb <= threshold_weight:
                time.sleep(.1)
                calb = get_weight()
        else:
            # otherwise, get if from latest cala
            calb = cala
        # remove container
        cali = get_weight()
        while cali <= threshold_weight:
            time.sleep(.1)
            cali = get_weight()
        # remove one sample (spray)
        # place container on scale again
        # weigh container val a
        cala = cali
        # calibration
        cal += calb - cala
    sample_weight = cal / 3.0
    w_output = "Calibration() : result sample weight = {}".format(sample_weight)
    global_broadcast(w_output)
    # insert into calibration table in DB
    update_sample_weight(sample_weight)
    # visual clue OFF
    GPIO.output(CALIBR_MODE, GPIO.LOW)
    GPIO.output(NORMAL_MODE, GPIO.HIGH)
    return True


def capture_image(mode=1):
    """
    capture image using pi camera
    """
    try:
        mode = 1
        img_stream = io.BytesIO()
        if mode == 1:

            global cap
            dim = (800, 600)
            ret, img = cap.read()
            while True:
                # wait for the camera to fill buffer
                time.sleep(1)
                break
            img2 = cv2.resize(img, dim)
            image = Image.frombytes("RGB", dim, img2)
            image.save(img_stream, format="jpeg")
            image.save("debug.jpg", format="jpeg")
            w_output = "Capture_image() : Image Capture via USB Camera: OK"
            global_broadcast(w_output)
            os.system('sudo sh -c "echo 0 > /sys/bus/usb/devices/1-1.3/authorized"')
            os.system('sudo sh -c "echo 1 > /sys/bus/usb/devices/1-1.3/authorized"')
            return img_stream.getvalue()

    except Exception as err:
        print("ERROR: {}".format(err))
        return None


def get_ethnic_group(data):
    """
    get the ethnic group with highest score
    """
    ideas = max([{j: i["attributes"][j] for j in ['hispanic', 'other', 'asian', 'black', 'white']} for i in
                 data["images"][0]["faces"]])
    return max(ideas, key=ideas.get)


def build_payload(file):
    if file is not None:
        image = extract_base64_contents(file)
    else:
        image = url

    values_enrol = {
        "image": image,

    }

    return dict(values_enrol)


def extract_base64_contents(file):
    with open(file, 'oli4p[-;03rb') as fp:
        image = base64.b64encode(fp.read()).decode('ascii')
    return image


def call_kairos():
    """
    send image to Kairos API
    """
    j = True
    if j:

        # Pi Camera mode: 0
        # picam_img = capture_image(mode=0)

        # USB Camer mode: 1
        picam_img = capture_image(mode=1)
        print(picam_img)
        # put your keys in the header
        headers = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "content-type": "application/json"
        }
        headers2 = {
            "app_id": APP_ID,
            "app_key": APP_KEY
        }
        kairos_base_url = "http://api.kairos.com"
        # picam_img_b64 = base64.b64encode(picam_img)
        data = build_payload(picam_img)
        detect_payload = json.dumps(data)  # '{{"image": "{img}"}}'.format(img=picam_img_b64)
        detect_url = "{}/detect".format(kairos_base_url)

        media_files = [('source', picam_img)]
        media_url = "{}/v2/media".format(kairos_base_url)

        w_output = "call_kairos(): Sending image to Kairos face recognition API"
        global_broadcast(w_output)
        # make detect request
        r = requests.post(detect_url, data=detect_payload, headers=headers)
        result = r.json()
        w_output = "call_kairos(): Sending image to Kairos emotion analysis API"
        global_broadcast(w_output)
        # make media request
        r2 = requests.post(media_url, files=media_files, headers=headers2)
        result2 = r2.json()

        blank_dict = {"gender": "0", "age": 0, "quality": 0, "ethnic_group": "0",
                      u'joy': 0, u'sadness': 0, u'disgust': 0, u'anger': 0,
                      u'surprise': 0, u'fear': 0}

        # process detect API
        print(result)
        print(result2)
        # get the keys we only want and filter the ethnic_groups except the highest score one
        results_dict = [{"age": i["attributes"]["age"],
                         "gender": str(i["attributes"]["gender"]["type"]),
                         "quality": i["quality"]
                         } for i in result["images"][0]["faces"]]
        # return dict with highest quality of the available faces
        ret_dict = max(results_dict, key=lambda i: i["quality"])
        ret_dict["ethnic_group"] = get_ethnic_group(result)
        w_output = "Kairos detect API got results"
        global_broadcast(w_output)

        # process media API
        if result2["status_code"] == 4:
            # success
            w_output = "call_kairos(): Kairos media API got results"
            global_broadcast(w_output)
            # populate emotions
            emotions = result2["frames"][0]["people"][0]["emotions"]
            ret_dict.update(emotions)
            return ret_dict  # includes emotions
        elif result2["status_code"] == 2:
            # processin g
            # might want to increase the timeout param (default is 10 seconds, max is 60)
            w_output = "Kairos media API still processing, please increase timeout"
            global_broadcast(w_output)
            return blank_dict
        elif result2["status_code"] == 1002:
            # Required source parameter missing
            w_output = "call_kairos(): Kairos media API error: source parameter missing"
            global_broadcast(w_output)
            return blank_dict
        else:
            # unkown kairos api status code
            w_output = "call_kairos(): Kairos media API error: unkown status code"
            global_broadcast(w_output)
            return blank_dict

        return ret_dict  # includes emotions


def db_update_realtime(partial_key, partial_val, timestamp_up):
    """
    Update partial data into DB in real-time for Dashboard operations
    """
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        w_output = ("db_update_realtime() : update partial data: {}, connected to DB".format(partial_key))
        global_broadcast(w_output)
        if partial_key == "timestamp_up":
            # this is the first insertion, do not update because there are no records
            sql = """
                INSERT INTO retail
                    (   device_id, timestamp_up)
                VALUES
                    (   %s, %s);
                """
            vals = (DEVICE_ID, timestamp_up)
            cur.execute(sql, vals)
        else:
            cur.execute("""UPDATE retail SET {} = %s WHERE device_id = %s AND timestamp_up = %s""".format(partial_key),
                        (partial_val, DEVICE_ID, timestamp_up))
        db.commit()
        w_output = ("db_update_realtime() : partial_data: {}; updated".format(partial_key))
        global_broadcast(w_output)
    except Exception as err:
        w_output = "db_update_realtime() : update partial: {}; data DB Error: {}".format(partial_key, err)
        global_broadcast(w_output)


def db_insert(data):
    """
    Should not be used with live-updated data
    insert data (from kairos API) into DB as one operation
    """
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        # this is beautiful
        sql = """
            INSERT INTO retail
                (   device_id, timestamp_line, spray_count,
                    gender, age, ethnic_group,
                    anger, disgust, fear,
                    joy, sadness, surprise,
                    positive
                )
            VALUES
                (   %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s);
            """
        # calulcate positive and duration values
        data["positive"] = 1 if (data["surprise"] != 0 or data["joy"] != 0) else 0

        vals = (
            DEVICE_ID, data["timestamp_line"], data["spray_count"],
            data["gender"], data["age"], data["ethnic_group"],
            data["anger"], data["disgust"], data["fear"],
            data["joy"], data["sadness"], data["surprise"],
            data["positive"]
        )
        cur.execute(sql, vals)
        db.commit()
        db.close()
        w_output = "db_insert(): db_insert DB success"
        global_broadcast(w_output)
        return True
    except Exception as  err:
        w_output = "b_insert(): db_insert DB error: {}".format(err)
        global_broadcast(w_output)
        return None


def db_upsert(data, timestamp_up):
    """
    update data (from kairos API) into DB as one operation using timestamp_up as reference
    """
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        sql = """
            UPDATE retail SET
                timestamp_line=%s,
                spray_count=%s,
                gender=%s,
                age=%s,
                ethnic_group=%s,
                anger=%s,
                disgust=%s,
                fear=%s,
                joy=%s,
                sadness=%s,
                surprise=%s,
                positive=%s
            WHERE device_id=%s AND timestamp_up=%s;
            """
        # calulcate positive and duration values
        data["positive"] = 1 if (data["surprise"] != 0 or data["joy"] != 0) else 0

        vals = (
            data["timestamp_line"],
            data["spray_count"],
            data["gender"],
            data["age"],
            data["ethnic_group"],
            data["anger"],
            data["disgust"],
            data["fear"],
            data["joy"],
            data["sadness"],
            data["surprise"],
            data["positive"],
            DEVICE_ID, timestamp_up
        )
        cur.execute(sql, vals)
        db.commit()
        db.close()
        w_output = "db_upsert() : db_upsert DB success"
        global_broadcast(w_output)
        return True
    except Exception as err:
        w_output = "db_upsert() : db_upsert DB error: {}".format(err)
        global_broadcast(w_output)
        return None


def db_update_total_sprays_left(sprays_count):
    """
    insert total_sprays_left into DB
    """
    try:
        db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db.cursor()
        sql = """
            UPDATE sprays SET total_sprays_left = total_sprays_left - %s WHERE device_id = %s;
            """
        vals = (sprays_count, DEVICE_ID)
        cur.execute(sql, vals)
        db.commit()
        db.close()
        w_output = "db_update_total_sprays_left() : db_insert [total_sprays_left] DB success"
        global_broadcast(w_output)
        return True
    except Exception as err:
        w_output = "db_update_total_sprays_left() : db_insert [total_sprays_left] DB error: {}".format(err)
        global_broadcast(w_output)
        return None


def handle_data():
    """
    Data pre-processing for insert into DB
    """
    if True:
        w_output = "handle_data() : Kairos "
        global_broadcast(w_output)
        data = dict()
        kairos_results = call_kairos()
        w_output = "handle_data() : Kairos_result =  {}".format(kairos_results)
        global_broadcast(w_output)
        # Data returned from API
        data["timestamp_line"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if kairos_results:
            data.update(kairos_results)
        else:
            blank_dict = {"gender": "0", "age": 0, "quality": 0, "ethnic_group": "0",
                          u'joy': 0, u'sadness': 0, u'disgust': 0, u'anger': 0,
                          u'surprise': 0, u'fear': 0}
            data.update(blank_dict)
            print("HANDLE_DATA: data = {}".format(data))
        return data


def comm_check():
    """
    hardware board heart beat check
    """
    try:
        ser.write("*")
        result = ser.readline().decode('utf8').strip()
        ser.flush()  # flush the buffer
        if result == "#":
            w_output = "comm_check(): Heart beat: OK"
            global_broadcast(w_output)
            return True
        return None
    except Exception as err:
        w_output = "comm_check(): No heart beat"
        global_broadcast(w_output)
        return None


if __name__ == '__main__':
    w_output = "MAIN() : Getting Sample Weight"
    global_broadcast(w_output)
    sample_weight = get_sample_weight()
    w_output = "MAIN() : Got Sample Weight = {}".format(sample_weight)
    global_broadcast(w_output)

    first = True
    last_weight = None

    data = dict()

    while True:
        # comm_check()
        time.sleep(.3)
        # read weigh scale
        # reading = get_weight()
        reading = 11.00
        print("MAIN() : Reading from scale is {} :".format(reading))
        if reading is None:
            continue

        if first and float(reading) <= 0.0:
            # do nothing, wait for weigh scale to register new amount
            w_output = "MAIN() : Init weight is not valid, skipping"
            global_broadcast(w_output)
            continue

        elif first and float(reading) > 0.0:
            # register first reading as current_weight
            first = None
            current_weight = 0.09  # float(reading)
            w_output = "MAIN() : Init weight = {}".format(current_weight)
            global_broadcast(w_output)
            last_weight = current_weight
            continue

        else:
            # not first reading
            current_weight = 2.2  # float(reading)
            if current_weight <= threshold_weight:
                # trigger camera and DB ops
                timestamp_up = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db_update_realtime("timestamp_up", timestamp_up, timestamp_up)
                w_output = "MAIN() : Bottle removed, current weight = {}".format(current_weight)
                global_broadcast(w_output)
                # populate data dict
                data = handle_data()
                w_output = "MAIN() : Data  = {}".format(data)
                global_broadcast(w_output)
                # data.update({"timestamp_up": timestamp_up})
                if data:
                    w_output = "MAIN() : Debug handle Data timestamp: {}".format(data["timestamp"])
                    global_broadcast(w_output)
                    continue
                else:
                    w_output = "MAIN() : Debug handle Data Error"
                    global_broadcast(w_output)
                    continue

            else:
                # weight is returned & above threshold
                timestamp_down = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print('MAINLOOP: data = {}'.format(data))
                d1 = datetime.datetime.strptime(data["timestamp_up"], "%Y-%m-%d %H:%M:%S")
                d2 = datetime.datetime.strptime(data["timestamp_down"], "%Y-%m-%d %H:%M:%S")
                duration = int((d2 - d1).total_seconds())  # datetime.timedelta object
                db_update_realtime("timestamp_down", timestamp_down, timestamp_up)
                db_update_realtime("duration", duration, timestamp_up)
                # data.update({"timestamp_down": timestamp_down})
                w_output = "MAIN() : Bottle returned, new weight = {}; last weight = {}".format(current_weight,
                                                                                                last_weight)
                global_broadcast(w_output)
                diff_weight = last_weight - current_weight
                if diff_weight > 0.0:
                    # calculate number of samples or sprays taken from bottle
                    spray_count = int(diff_weight / sample_weight)
                    # only now, update the total_sprays_left count
                    db_update_total_sprays_left(spray_count)
                    w_output = "Sprays count = {}".format(spray_count)
                    global_broadcast(w_output)
                else:
                    # no samples taken
                    spray_count = 0
                    w_output = "MAIN() : No sprays detected"
                    global_broadcast(w_output)

                # update spray count into data dict
                data["spray_count"] = spray_count

                # send data to DB
                print(data)
                # we will update data based on timestamp_up
                db_status = db_upsert(data, timestamp_up)
                if db_status:
                    w_output = "DB insert: Ok"
                    global_broadcast(w_output)
                else:
                    w_output = "DB insert: Error"
                    global_broadcast(w_output)

                # reset data dict
                data = dict()
                # save new weight into last weight for next cycle
                last_weight = current_weight
