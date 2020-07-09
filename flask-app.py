import jsonpickle
from flask import Flask, request, Response, make_response
import requests
import numpy as np
import cv2
import Class_Face_detection
import train_main
import os
import time
import face_recognition
from flask_cors import CORS, cross_origin
import base64
from PIL import Image
from io import BytesIO
from Database import Database
import json

app = Flask(__name__)
# Configure a secret SECRET_KEY

CORS(app)

cors = CORS(app, resources={r"/*": {"origins": "*"}})
db = Database()

def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


detection = Class_Face_detection.Detection()
train = train_main.Train()
print('Initilize done.... ')
sampleNum = 0


# add students in data base
@app.route("/fetchAllStudents", methods=['POST'])
def fetchAllStudents():
    student_ids = []
    key = request.json['ID']
    link = 'http://192.168.10.28:4001/api/v1/Users/PickListByCustomerID/{}'.format(key)
    payload = {}
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", link, headers=headers, data=payload)
    result = response.json()
    print(result["Result"][0])
    for x in result["Result"]:
        student_ids.append(x["ProfileIdFK"])
    for x in student_ids:
        bol = db.InsertStudent(x, key, 0)
        print(bol)
    #["ProfileIdFK"])
    return response.text
    pass

@app.route("/status/fetchStatus", methods=['POST'])
def fetchStatus():
    try:
        key = request.json['ID']
        data = db.get_all_users(key)

        response = {'data': '{}'.format(data),
                     'message':'Done'
                    }
        response_pickled = json.dumps(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
        pass
    except Exception as error:
        print('Error in Fetching Student status from DB : {}'.format(error))
        response = {
                    'message': 'Wrong'
                    }
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    pass

def getListOfFiles(dirName):
    listOfFile = os.listdir(dirName)
    return listOfFile

@app.route("/qa", methods=['POST'])
def _getImages():
    print("QA testing Images now !!")
    image = request.json['File']['_imageAsDataUrl']
    image = image_spliter(image)
    im = np.array(image)
    image = detection.detect_picture(im)
    # build a response dict to send back to client
    if len(image) > 0:
        response = {'message': '{}'.format(image[0])
                }
    else:
        respose = {'message' : 'No Image!!'}
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route("/check_training_pending", methods=["GET"])
def check_training_peding():
    folderPath = 'software_data/'
    if not os.path.exists(folderPath):
        response = {'message': 'Error in Finding Path!!'
                    }
    else:
        listOfFiles = getListOfFiles(folderPath)
        print(listOfFiles)
        response = {'message': '{}'.format(listOfFiles)
                    }
        # os.makedirs(folderPath)
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route("/check_image", methods=['POST'])
def getImages():
    print(request.data)
    # convert string of image data to uint8
    nparr = np.fromstring(request.data, np.uint8)
    print(nparr)
    # decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image = detection.detect_picture(img)
    # build a response dict to send back to client
    response = {'message': '{}'.format(image[0])
                }
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


def image_spliter(string):
    if len(string) > 0:
        image = string[23:]
        image = Image.open(BytesIO(base64.b64decode(image)))
        return image


@app.route("/get_train_images", methods=['POST'])            # training from client side application
@cross_origin()
def gettrainImages():
    print("Getting new images from client side....")
    image = request.json['File']['_imageAsDataUrl']
    key = request.json['ID']
    number = request.json['number']
    cus_id = request.json['CID']
    folderName = str(cus_id) + "/" + str(key)  # creating the person or user folder
    folderPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "software_data/" + folderName)
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    image = image_spliter(image)
    result = detection.check_faces_in_training_pictures(image)
    print('Result getting from face detecting module = {}'.format(result))
    if result == 'True':
        db.UpdateStudent(key,cus_id,1)
        image.save(folderPath + "/ActiOn_" + str(number) + ".jpeg", "JPEG")
        time.sleep(0.01)
        # image = detection.detect_picture(img)
        response = {'message': 'Done'
                    }
    else:
        response = {'message': 'Wrong'
                    }
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route("/start_training", methods=["GET"])
def start_training():
    response = train.training()
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")
    pass



if __name__ == "__main__":
    #app.run(debug=True, host="127.0.0.1", port=5001)
    app.run(debug=True)
