from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#import tensorflow as tf
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from scipy import misc
import cv2
import numpy as np
import facenet
import detect_face
import os
import time
import pickle
import datetime

class Recognition:

    def __init__(self):
        self.modeldir = './model/20170511-185253.pb'
        self.classifier_filename = './class/classifier.pkl'
        self.npy = './npy'
        self.train_img = "./train_img"
        self.c = 0
        with tf.Graph().as_default():
            gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
            self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
            with self.sess.as_default():
                self.pnet, self.rnet, self.onet = detect_face.create_mtcnn(self.sess, self.npy)
                print('On init Pnet = {} \n Rnet = {} \n Onet = {} \n'.format(self.pnet, self.rnet, self.onet))
                self.minsize = 20  # minimum size of face
                self.threshold = [0.6, 0.7, 0.7]  # three steps's threshold
                self.factor = 0.709  # scale factor
                self.margin = 4
                self.frame_interval = 3
                self.batch_size = 1000
                self.image_size = 182
                self.input_image_size = 160
                self.accuracy = 0.8

                self.HumanNames = os.listdir(self.train_img)
                self.HumanNames.sort()

                print('Loading Modal')
                facenet.load_model(self.modeldir)
                self.images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
                self.embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
                self.phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
                self.embedding_size = self.embeddings.get_shape()[1]

                classifier_filename_exp = os.path.expanduser(self.classifier_filename)
                with open(classifier_filename_exp, 'rb') as infile:
                    (self.model, self.class_names) = pickle.load(infile)

    def check_rec_image(self, frame):
        name = []
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)  # resize frame (optional)
        curTime = time.time() + 1  # calc fps
        timeF = self.frame_interval

        if (self.c % timeF == 0):
            find_results = []
            if frame.ndim == 2:
                frame = facenet.to_rgb(frame)
            frame = frame[:, :, 0:3]
            bounding_boxes, _ = detect_face.detect_face(frame, self.minsize, self.pnet, self.rnet, self.onet,
                                                        self.threshold, self.factor)
            nrof_faces = bounding_boxes.shape[0]
            print('Detected_FaceNum: %d' % nrof_faces)
            if nrof_faces >= 0:
                det = bounding_boxes[:, 0:4]
                img_size = np.asarray(frame.shape)[0:2]
                cropped = []
                scaled = []
                scaled_reshape = []
                bb = np.zeros((nrof_faces, 4), dtype=np.int32)

                for i in range(nrof_faces):
                    emb_array = np.zeros((1, self.embedding_size))

                    bb[i][0] = det[i][0]
                    bb[i][1] = det[i][1]
                    bb[i][2] = det[i][2]
                    bb[i][3] = det[i][3]

                    cropped.append(frame[bb[i][1]:bb[i][3], bb[i][0]:bb[i][2], :])
                    cropped[i] = facenet.flip(cropped[i], False)
                    scaled.append(misc.imresize(cropped[i], (self.image_size, self.image_size), interp='bilinear'))
                    scaled[i] = cv2.resize(scaled[i], (self.input_image_size, self.input_image_size),
                                           interpolation=cv2.INTER_CUBIC)
                    scaled[i] = facenet.prewhiten(scaled[i])
                    scaled_reshape.append(scaled[i].reshape(-1, self.input_image_size, self.input_image_size, 3))
                    feed_dict = {self.images_placeholder: scaled_reshape[i], self.phase_train_placeholder: False}
                    emb_array[0, :] = self.sess.run(self.embeddings, feed_dict=feed_dict)
                    predictions = self.model.predict_proba(emb_array)
                    print(predictions)
                    best_class_indices = np.argmax(predictions, axis=1)
                    best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
                    # print("predictions")
                    print(best_class_indices, ' with accuracy ', best_class_probabilities)

                    # print(best_class_probabilities)
                    if best_class_probabilities > self.accuracy:
                        cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 255, 0), 2)  # boxing face

                        # plot result idx under box
                        text_x = bb[i][0]
                        text_y = bb[i][3] + 20
                        print('Result Indices: ', best_class_indices[0])
                        print(self.HumanNames)
                        for H_i in self.HumanNames:
                            if self.HumanNames[best_class_indices[0]] == H_i:
                                result_names = self.HumanNames[best_class_indices[0]]
                                name.append(result_names)
        return name



