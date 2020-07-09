import cv2  # openCV
import numpy as np  # for numpy arrays
import sqlite3
import dlib
import os  # for creating folders

Camera_number = 1

# cap = cv2.VideoCapture('video_for_training.mp4')
cap = cv2.VideoCapture(Camera_number)
detector = dlib.get_frontal_face_detector()
font = cv2.FONT_HERSHEY_SIMPLEX  # the font of text on face recognition

name = input("Enter student's name : ")


folderName = "" + name  # creating the person or user folder
folderPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "train_img_temp/" + folderName)
if not os.path.exists(folderPath):
    os.makedirs(folderPath)

sampleNum = 0
while (True):
    try:
        ret, img = cap.read()  # reading the camera input
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Converting to GrayScale
        dets = detector(img, 0)
        print(len(dets))
        if len(dets)>1:
            print('Warning !! more than 1 faces are detected!!')
        else:
            for i, d in enumerate(dets):  # loop will run for each face detected
                sampleNum += 1
                try:
                    cv2.imwrite(folderPath + "/ActiOn_" + str(sampleNum) + ".jpg",
                            img[d.top()-50:d.bottom()+50, d.left()-50:d.right()+50])  # Saving the faces
                    cv2.rectangle(img, (d.left(), d.top()), (d.right(), d.bottom()), (0, 255, 0),
                              2)  # Forming the rectangle
                    cv2.putText(img,
                            "Capturing: " + str(sampleNum),
                            (d.left(), d.bottom()),
                            font, 1, (255, 255, 255), 1, cv2.LINE_AA
                            )
                except Exception as error :
                    print('Excetption in program while taking images: ',error)
                    pass
                cv2.waitKey(1)  # waiting time of 200 milisecond
            cv2.imshow('frame', img)  # showing the video input from camera on window
            cv2.waitKey(1)
            if (sampleNum >= 200):  # will take 200 faces
                break


    except Exception as error:
        print('Faulty pic capture! : {}'.format(error))
print('All done perfect!')
cap.release()  # turning the webcam off
cv2.destroyAllWindows()  # Closing all the opened windows
