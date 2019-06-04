# -*- coding: utf-8 -*-
"""layer1-canidae

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pe9BGoGWPM6WO07Qyw9NpOq5Bxor7jWR
"""

import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import matplotlib
matplotlib.use("Agg")

import keras
from keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from keras.layers import Dense, Flatten, LocallyConnected1D, Reshape
from keras import optimizers
from keras.models import Sequential, Model
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import backend as K

import numpy as np
import pandas as pd
import h5py

import random
import math

def get_classes_list(basepath, classes_ind_list):
  '''get classes list (names of subdirectories) from an index list'''
  classes = os.listdir(basepath)
  classes_list = [classes[k] for k in classes_ind_list]      
  print ('Number of classes: ', len(classes_list))
  return classes_list

#Magic numbers
num_epochs = 100
bs = 64
img_rows = 224
img_cols = 224
flatten_shape = 1000

#Build training&validation data generator
with open('group_canidae.txt', 'r') as f:
    x = f.read().split('\n')
cani_ind = [int(i) for i in x ]    

train_data_dir = '/mnt/fast-data16/datasets/ILSVRC/2012/clsloc/train/'
canidae_list = get_classes_list(train_data_dir, cani_ind)

train_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split = 0.1)

#test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size = (img_rows, img_cols),
        batch_size = bs,
        classes = canidae_list,
        class_mode = 'categorical',
        subset='training')

validation_generator = train_datagen.flow_from_directory(
    train_data_dir, # same directory as training data
    target_size=(img_rows, img_cols),
    batch_size= bs,
    classes = canidae_list,
    class_mode='categorical', 
    subset ='validation') # set as validation data

#Customize a constraint class that clip w to be [K.epsilon(), inf]
from keras.constraints import Constraint

class CustomConstraint (Constraint):
  
    def __call__(self, w):      
        new_w = K.clip(w, K.epsilon(), None)
        return new_w

#Build the model
vgg16_model = VGG16(weights = 'imagenet', include_top=True, input_shape = (img_rows, img_cols, 3))

for layer in vgg16_model.layers:
    layer.trainable = False
    
model = Sequential()
model.add(vgg16_model)
model.add(Reshape(input_shape=(flatten_shape,), target_shape=(flatten_shape,1)))
model.add(LocallyConnected1D(1,1, use_bias = False, kernel_constraint= CustomConstraint()))
model.add(Flatten())

model.compile(loss='categorical_crossentropy', 
              optimizer='adam', 
              metrics=['accuracy'])

model.summary()

#Callbacks
callbacks = [EarlyStopping(monitor='val_loss', patience=1, verbose = 1),
             ModelCheckpoint(filepath='layer1-canidae-model.h5', monitor='val_loss', save_best_only=True)]
#Training
step_size_train=train_generator.n//train_generator.batch_size
step_size_validation=validation_generator.n//validation_generator.batch_size

model.fit_generator(
        train_generator,
        steps_per_epoch=step_size_train,
        epochs=num_epochs,
        callbacks = callbacks, 
        validation_data=validation_generator, 
        validation_steps=step_size_validation)
