import keras
import numpy as np


class My_Custom_Generator(keras.utils.Sequence):

    def __init__(self, temp_sequences, labels, batch_size):
        self.sequences = temp_sequences
        self.labels = labels
        self.batch_size = batch_size

    def __len__(self):
        return (np.ceil(len(self.sequences) / float(self.batch_size))).astype(np.int)

    def __getitem__(self, idx):
        batch_x = self.sequences[idx * self.batch_size: (idx + 1) * self.batch_size]
        batch_y = self.labels[idx * self.batch_size: (idx + 1) * self.batch_size]

        return np.array(batch_x), np.array(batch_y)
