# -*- coding: UTF-8 -*-
import numpy as np
from imutils import paths
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
import cv2
import os

class Dataset(object):
    def __init__(self, path, one_hot=True, split=0):
        # grab the list of images in our dataset directory, then initialize
        # the list of data (i.e., images) and class images
        print("[INFO] loading images...")
        imagePaths = list(paths.list_images(path))
        train_imagePaths = list(paths.list_images(path+os.path.sep+'train'))
        test_imagePaths = list(paths.list_images(path+os.path.sep+'test'))
        data = []
        labels = []
        test_data = []
        test_labels = []

        # loop over the image paths
        for imagePath in train_imagePaths:
            # extract the class label from the filename
            label = imagePath.split(os.path.sep)[-2]

            # load the image, swap color channels, and resize it to be a fixed
            # 224x224 pixels while ignoring aspect ratio
            image = cv2.imread(imagePath)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (224, 224))

            # update the data and labels lists, respectively
            data.append(image)
            labels.append(label)

            # convert the data and labels to NumPy arrays while scaling the pixel
            # intensities to the range [0, 255]
        data = np.array(data) / 255.0
        labels = np.array(labels)

            # perform one-hot encoding on the labels
        lb = LabelBinarizer()
        labels = lb.fit_transform(labels)
        labels = to_categorical(labels)
        (self.x_train, self.x_val, self.y_train, self.y_val) = train_test_split(data, labels,
            test_size=50, stratify=labels, random_state=42)        

        # test data process
        for imagePath in test_imagePaths:
            # extract the class label from the filename
            label = imagePath.split(os.path.sep)[-2]

            # load the image, swap color channels, and resize it to be a fixed
            # 224x224 pixels while ignoring aspect ratio
            image = cv2.imread(imagePath)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (224, 224))

            # update the data and labels lists, respectively
            test_data.append(image)
            test_labels.append(label)

        # convert the data and labels to NumPy arrays while scaling the pixel
        # intensities to the range [0, 255]
        self.x_test = np.array(test_data) / 255.0
        test_labels = np.array(test_labels)

        # perform one-hot encoding on the labels
        lb = LabelBinarizer()
        test_labels = lb.fit_transform(test_labels)
        self.y_test = to_categorical(test_labels)

        print("Dataset: train-%d, val-%d, test-%d" % (len(self.x_train), len(self.x_val), len(self.x_test)))

        