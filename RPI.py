from __future__ import print_function
import Class_Face_Recognition
import requests
import cv2
import sqlite3
import datetime as dt
import json


cam_number  = 0
class Detection:
    def __init__(self):
        recent_time = dt.datetime.now()
        self.cascadePath = "haarcascade_frontalface_alt.xml"
        self.faceCascade = cv2.CascadeClassifier(self.cascadePath)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.addr = 'http://192.168.8.100:5001'
        self.test_url = self.addr + '/check_image'
        self.recognition = Class_Face_Recognition.Recognition()
        self.url = "http://192.168.10.28:4007/api/v1/AttendanceMaster/AttendenceOnGivenDateCamera?ClientId=60105&TodayDateVal=20200319&StartTime=0900&RoomId=70189"
        self.url_post = "http://192.168.10.28:4007/api/v1/Update/AttendanceCamera/"
        self.format = ''
        self.students = []
        self.attendent_students=[]
        self.get_students()
        # prepare headers for http request
        self.content_type = 'image/jpeg'
        self.headers = {'content-type': self.content_type}
    def detect_picture(self):
        try:
            crop = []
            _label = []
            #im = picture
            im = cv2.imread('video/SHAHB/ActiOn_226.jpg')
            #im = cv2.imread('video/saad/ActiOn_225.jpg')
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            # faces=faceCascade.detectMultiScale(gray, 1.2,5)
            faces = self.faceCascade.detectMultiScale(gray)
            if len(faces) > 0:
                print(faces)

                for (x, y, w, h) in faces:
                    cv2.rectangle(im, (x, y), (x + w, y + h), (0, 260, 0), 2)
                    # cv2.putText(im, str('MISBAH'), (x,y-40), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                    crop.append(im[y:y + h, x:x + w])
                for img in crop:
                    img = cv2.resize(img,(160,160))
                    cv2.imshow("frame",img)
                    _label = self.recognition.check_rec_image(img)
                i = 0
                for face_names in _label:
                    cv2.putText(im, face_names, (10 + i, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0),
                                thickness=1, lineType=2)
                    i += 1
                    print(face_names)
                while True:
                    cv2.imshow('frames', im)
                    k = cv2.waitKey(1)
                    if k == ord('q'):
                        cv2.destroyAllWindows()
                        break

        except Exception as error:
            print('Error ##### : {}'.format(error))
    def post_students_data(self):
        payload = {}
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(self.url_post, data=json.dumps(self.format), headers=headers)
        print('response from post method {}'.format(response))
    def get_students(self):
        payload = {}
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", self.url, headers=headers, data=payload)
        print(response.text)
        result = json.loads(str(response.text))
        self.format = result["Result"]
        print(self.format)
        for x in result["Result"]:
            self.students.append(x["LearnerId"])



        pass
    def detect_face(self, num):

        streaming = cv2.VideoCapture(num)
        print(self.students)
        while True:
            try:
                crop = []
                _label = []
                _, im = streaming.read()
                gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                # faces=faceCascade.detectMultiScale(gray, 1.2,5)
                faces = self.faceCascade.detectMultiScale(gray)
                cv2.imshow("Frame", im)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                if len(faces) > 0:
                    print('face detected')
                    _, img_encoded = cv2.imencode('.jpg', im)
                    # send http request with image and receive response
                    response = requests.post(self.test_url, data=img_encoded.tostring(), headers=self.headers)
                    decode_response = response.json()
                    _student = decode_response["message"]
                    print('Student found  = {}'.format(_student))
                    if int(_student) in self.students: # checking orignal list
                        if _student in self.attendent_students:
                            print('student {} Already exit'.format(_student))
                        else:
                            self.attendent_students.append(_student)
                    else:
                        print('in list {} is not in {}'.format(self.students,_student))
                    print(self.attendent_students)
                    for x in self.attendent_students:
                        print('chaging attendence')
                        for x in self.format:
                            if x["LearnerId"] == int(_student):
                                print('changing attend to 1 of {}'.format(_student))
                                x["Attnd"] = 1
                                print('Attendence change to {}'.format(x["Attnd"]))
                    print(self.format)
                    self.post_students_data()








            except Exception as error:
                print('EEEEEEEEEEEEEEEEEEEEEeroor : {}'.format(error))

        streaming.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    detect = Detection()
    detect.detect_face(cam_number)
    #detect.detect_picture()
