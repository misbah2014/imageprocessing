import cv2
import os
import datetime
import Class_Face_Recognition
import numpy as np

class Detection:
    def __init__(self):
        self.cascadePath = 'HaarCascade/haarcascade_frontalface_alt2.xml' # best match after test
        self.faceCascade = cv2.CascadeClassifier(self.cascadePath)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.recognition = Class_Face_Recognition.Recognition()

    def check_faces_in_training_pictures(self, picture):
        try:
            crop = []
            _label = []
            im = np.array(picture)
            #im = cv2.UMat(picture)
            #cv2.cvtColor(cv2.UMat(im), cv2.COLOR_RGB2GRAY)
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            # faces=faceCascade.detectMultiScale(gray, 1.2,5)
            faces = self.faceCascade.detectMultiScale(gray, 1.1, 2)
            # faces = self.faceCascade.detectMultiScale3(gray,1.2,1)
            if len(faces) == 1:
                return 'True'
            elif len(faces) > 1:
                return 'False'
            else:
                return 'False'

        except Exception as error:
            return error

    def detect_picture(self,picture):
        try:
            crop = []
            _label = []
            im = picture
            #im = cv2.imread('video/SHAHB/ActiOn_226.jpg')
            #im = cv2.imread('video/saad/ActiOn_225.jpg')
            #im = cv2.imread('Sample_images/optyyl2.jpg')
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            # faces=faceCascade.detectMultiScale(gray, 1.2,5)
            faces = self.faceCascade.detectMultiScale(gray,1.1,2)
            #faces = self.faceCascade.detectMultiScale3(gray,1.2,1)
            if len(faces) > 0:
                print(faces)

                for (x, y, w, h) in faces:
                    cv2.rectangle(im, (x, y), (x + w, y + h), (0, 260, 0), 2)
                    # cv2.putText(im, str('MISBAH'), (x,y-40), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                    crop.append(im[y:y + h, x:x + w])
                for img in crop:
                    img = cv2.resize(img,(160,160))
                    _label += self.recognition.check_rec_image(img)
                    print('Printing labels are as : {}'.format(_label))
                    if len(_label) > 0:
                        for personName in _label:
                            folderName = "" + personName  # creating the person or user folder
                            folderPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                           "test-images/" + folderName)
                            if not os.path.exists(folderPath):
                                os.makedirs(folderPath)
                            date_string = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
                            try:
                                cv2.imshow("frame", im)
                                cv2.imwrite(folderPath + "/"+ date_string+".jpg", im)
                            except Exception as error:
                                print('Error  {}'.format(error))
                    else:
                        folderName = "Unknown"  # creating the person or user folder
                        folderPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  "test-images/" + folderName)
                        if not os.path.exists(folderPath):
                            os.makedirs(folderPath)
                        date_string = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
                        cv2.imwrite(folderPath + "/"+date_string + ".jpg", im)
                        _label += ['UNKNOWN']
            else:
                print('No face detected yet')
            return _label



        except Exception as error:
            print('Error ##### : {}'.format(error))

    def detect_face(self, num):
        streaming = cv2.VideoCapture(num)

        while True:
            try:
                crop = []
                _label = []
                _, im = streaming.read()
                gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                # faces=faceCascade.detectMultiScale(gray, 1.2,5)
                faces = self.faceCascade.detectMultiScale(gray,1.1,2)
                if len(faces) > 0:
                    print(faces)

                    for (x, y, w, h) in faces:
                        cv2.rectangle(im, (x, y), (x + w, y + h), (0, 260, 0), 2)
                        # cv2.putText(im, str('MISBAH'), (x,y-40), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                        crop.append(im[y:y + h, x:x + w])
                    for img in crop:
                        _label += self.recognition.check_rec_image(img)
                    i = 0
                    for face_names in _label:
                        cv2.putText(im, face_names, (10 + i, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0),
                                    thickness=1, lineType=2)
                        i += 1
                        print(face_names)
                    cv2.imshow('frames', im)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except Exception as error:
                print('Eeroor : {}'.format(error))

        streaming.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    detect = Detection()
    #detect.detect_face(0)
    names = detect.detect_picture()
    for name in names:
        print('Result names are : {}'.format(name))
"""
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
                    """