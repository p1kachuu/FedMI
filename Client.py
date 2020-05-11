# -*- coding: UTF-8 -*-
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import socket
from PaillierT import *
from Model import vgg16_model
from Dataset import Dataset

class Client:
    def __init__(self, init_lr, client_id, client_ip, path):

        # client attribute
        self.model = vgg16_model()
        self.cid = client_id
        self.ip = client_ip
        self.dataset = Dataset(path)  
        self.history = {"loss":[], "val_loss":[], "accuracy":[], "val_accuracy":[]}

        # compile our model
        print("[INFO] compiling model...")
        #opt = Adam(lr=init_lr, decay=init_lr / epochs)
        opt = Adam(lr=init_lr)
        self.model.compile(loss="binary_crossentropy", optimizer=opt,
        metrics=["accuracy"])

    def train_epoch(self, BS=8):
        """
            Train one client with its own data for one epoch 
            cid: Client id
        """
        trainX = self.dataset.x_train
        trainY = self.dataset.y_train
        valX = self.dataset.x_val
        valY = self.dataset.y_val 

        # initialize the training data augmentation object
        trainAug = ImageDataGenerator(
             rotation_range=15,
             fill_mode="nearest")

        # train the head of the network
        # print("[INFO] training model...")
        print("")
        H = self.model.fit(
            trainAug.flow(trainX, trainY, batch_size=BS),
            #trainX, trainY, batch_size=BS,
            steps_per_epoch=len(trainX) // BS,
            validation_data=(valX, valY),
            epochs=1,
            verbose=1
            )
        print("")
        self.history["loss"].append(H.history["loss"][0])
        self.history["val_loss"].append(H.history["val_loss"][0])
        self.history["accuracy"].append(H.history["accuracy"][0])
        self.history["val_accuracy"].append(H.history["val_accuracy"][0])

    def plot_history(self, path):
        # plot the training loss and accuracy
        N = len(self.history["loss"])
        plt.style.use("ggplot")
        plt.figure()
        plt.plot(np.arange(0, N), self.history["loss"], label="train_loss")
        plt.plot(np.arange(0, N), self.history["val_loss"], label="val_loss")
        plt.plot(np.arange(0, N), self.history["accuracy"], label="train_acc")
        plt.plot(np.arange(0, N), self.history["val_accuracy"], label="val_acc")
        plt.title("Training Loss and Accuracy on COVID-19 Dataset")
        plt.xlabel("Epoch #")
        plt.ylabel("Loss/Accuracy")
        plt.legend(loc="lower left")
        plt.savefig(path)

    def test_model(self, BS=8):
        """ make predictions on the testing set """
        # load test dataset
        testX = self.dataset.x_test
        testY = self.dataset.y_test

        print("[INFO] evaluating network...")
        predIdxs = self.model.predict(testX, batch_size=BS)

        # for each image in the testing set we need to find the index of the
        # label with corresponding largest predicted probability
        predIdxs = np.argmax(predIdxs, axis=1)

        # show a nicely formatted classification report
        print(classification_report(testY.argmax(axis=1), predIdxs,
	        target_names=['covid', 'normal']))

        # compute the confusion matrix and and use it to derive the raw
        # accuracy, sensitivity, and specificity
        cm = confusion_matrix(testY.argmax(axis=1), predIdxs)
        total = sum(sum(cm))
        acc = (cm[0, 0] + cm[1, 1]) / total
        sensitivity = cm[0, 0] / (cm[0, 0] + cm[0, 1])
        specificity = cm[1, 1] / (cm[1, 0] + cm[1, 1])

        # show the confusion matrix, accuracy, sensitivity, and specificity
        print(cm)
        print("acc: {:.4f}".format(acc))
        print("sensitivity: {:.4f}".format(sensitivity))
        print("specificity: {:.4f}".format(specificity))

    def save_model(self, model_path):
        """ Save trained model """
        print("[INFO] client_{}:saving client weights...".format(self.cid))
        self.model.save(model_path, save_format='h5')

    def set_weights(self, global_weights):
        """ Assign all of the variables with global vars """
        print("[INFO] client_{}:setting global weights...".format(self.cid))
        base_weights = self.model.get_weights()[:26]
        # print("####################解密后###########################")
        # print(global_weights[1])
        self.model.set_weights(base_weights+list(global_weights))

    def get_weights(self):
        """ Return all of the variables list """
        print("[INFO] client_{}:getting client weights...".format(self.cid))
        client_weights = self.model.get_weights()[26:]
        # print("#####################加密前###########################")
        # print(client_weights[1])
        return client_weights
    
    def encrypt_weights(self, client_weights, public_key):
        """ Encrypt client weights """
        print("[INFO] client_{}:encrypting weights....".format(self.cid))
        en_params = []
        for layer in client_weights:
            shape = layer.shape
            temp_arr = np.array([public_key.encrypt(float(x)) for x in np.nditer(layer)])
            en_params.append(temp_arr.reshape(shape))
        return np.array(en_params)
    
    def encrypt_weights_with_key_div(self, weights, public_key, acc=1000000):
        """ Encrypt client weights with paillier kety division"""
        print("[INFO] client_{}:encrypting weights....".format(self.cid))
        en_params = []
        for i in range(len(weights)):
            weights[i] = weights[i] * acc
            weights[i] = weights[i].astype(np.int)
            shape = weights[i].shape
            temp_arr = np.array([encrypt(int(x), public_key) for x in np.nditer(weights[i])])
            en_params.append(temp_arr.reshape(shape))
        return np.array(en_params)

    def decrypt_global_weights(self, en_params, private_key):
        """ Decrypt global weights """
        print("[INFO] client_{}:decrypting weights....".format(self.cid))
        de_params = []
        for layer in en_params:
            shape = layer.shape
            temp_arr = np.array([private_key.decrypt(x[()]) for x in np.nditer(layer, flags=['refs_ok'])])
            de_params.append(temp_arr.reshape(shape))
        return de_params
    
    def decrypt_global_weights_with_key_div(self, c0_params, en_params, sk1, pk, acc=1000000):
        """ Decrypt global weights with paillier kety division"""
        print("[INFO] client_{}:decrypting weights....".format(self.cid))
        c1_params = []
        de_params = []
        for i in range(len(en_params)):
            shape = en_params[i].shape
            temp_arr = np.array([share_dec(int(x), pk, sk1) for x in np.nditer(en_params[i], flags=['refs_ok'])])
            c1_params.append(temp_arr.reshape(shape))
        assert len(c0_params)==len(c1_params)
        for i in range(len(en_params)):
            shape = en_params[i].shape
            temp_arr = np.array([dec_with_shares(int(s0), int(s1), pk) for (s0, s1) in zip(np.nditer(c0_params[i], flags=['refs_ok']), np.nditer(c1_params[i], flags=['refs_ok']))])
            temp_arr = temp_arr / acc
            de_params.append(temp_arr.reshape(shape))
        return de_params
