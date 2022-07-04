import cv2
import numpy as np
import os
from matplotlib import pyplot as plt
import time
import mediapipe as mp
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
import json
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Bidirectional
from tensorflow.keras.callbacks import TensorBoard, EarlyStopping
from mycustomgenerator import My_Custom_Generator
import pickle

DATA_PATH = os.path.join('WLASL2000_KP')

with open('start_kit/WLASL_v0.3.json', 'r') as f:
    data1 = json.load(f)


def combine_keypoints():
    sequences, labels = [], []
    glosses = []

    for gloss in data1:
        glosses.append(gloss['gloss'])

    label_map = {label: num for num, label in enumerate(glosses)}
    for gloss in tqdm(data1):

        for inst in gloss['instances']:

            window = []
            # print(gloss['gloss'], inst['video_id'], len(os.listdir(os.path.join(DATA_PATH, gloss['gloss'], inst['video_id']))))

            for frame_num in range(len(os.listdir(os.path.join(DATA_PATH, gloss['gloss'], inst['video_id'])))):
                res = np.load(os.path.join(DATA_PATH, gloss['gloss'], inst['video_id'], "{}.npy".format(frame_num))
                              , allow_pickle=True)
                # print(os.path.join(DATA_PATH, gloss['gloss'], inst['video_id'], "{}.npy".format(frame_num)))
                # print(frame_num)
                window.append(res)
                # break
            sequences.append(window)
            labels.append(label_map[gloss['gloss']])
        # break
    # break
    return sequences, labels


def append_zero_arrays(x):
    if len(x) < 250:
        zero_array = np.zeros((1662,))
        while len(x) != 250:
            x.append(zero_array)
    return x


def createTrainTestData(temp_sequences, Y, X_train, Y_train, X_test, Y_test, count, i):
    while count != len(data1) - 1:  # for gloss in data1:    #
        for inst in data1[count]['instances']:

            print(data1[count]['gloss'], inst['video_id'], inst['split'])
            if inst['split'] == 'train' or inst['split'] == 'val':
                # print("train",i)
                X_train.append(np.array(temp_sequences[i], dtype=np.float16))
                Y_train.append(np.array(Y[i], dtype=np.int8))

            elif inst['split'] == 'test':
                # print("test",i)
                X_test.append(np.array(temp_sequences[i], dtype=np.float16))
                Y_test.append(np.array(Y[i], dtype=np.int8))

            i += 1

        count += 1
        if count == 1000:
            break

    X_train = np.array(X_train, dtype=np.float16)
    Y_train = np.array(Y_train, dtype=np.int8)
    X_test = np.array(X_test, dtype=np.float16)
    Y_test = np.array(Y_test, dtype=np.int8)

    return X_train, Y_train, X_test, Y_test


def main():
    X_train = []
    X_test = []
    Y_train = []
    Y_test = []

    count = 0
    i = 0

    # sequences, labels = combine_keypoints()
    with open('sequences.txt', 'rb') as f:
        sequences = pickle.load(f)
    labels = np.load('labels.npy')
    print("Got sequences and labels.")

    temp_sequences = []
    for seq in sequences:
        temp_sequences.append(append_zero_arrays(seq))

    Y = to_categorical(labels).astype(int)
    X_train, Y_train, X_test, Y_test = createTrainTestData(temp_sequences, Y, X_train, Y_train, X_test, Y_test, count,
                                                           i)

    print("Got training and test sets.")

    my_training_batch_generator = My_Custom_Generator(X_train, Y_train, 2)
    my_validation_batch_generator = My_Custom_Generator(X_test, Y_test, 2)

    log_dir = os.path.join('Logs')
    tb_callback = TensorBoard(log_dir=log_dir)
    es_callback = EarlyStopping(monitor='loss', patience=10)

    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(300, 1662)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(len(data1), activation='softmax'))
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    print(model.summary())

    # model.fit(X_train, Y_train, batch_size=8, epochs=2000, callbacks=[tb_callback], workers=4, use_multiprocessing=True)
    model.fit_generator(generator=my_training_batch_generator,
                        steps_per_epoch=int(11292 // 2),
                        epochs=10,
                        verbose=1,
                        validation_data=my_validation_batch_generator,
                        validation_steps=int(1876 // 2))

    res = model.predict(X_test)
    print('===============================================>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    print(res)

    model.save('slr_first.h5')


if __name__ == "__main__":
    main()
