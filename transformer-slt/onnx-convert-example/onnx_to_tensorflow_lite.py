import sys
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import onnx
from collections import OrderedDict
import tensorflow as tf
from torch.autograd import Variable
from onnx_tf.backend import prepare

# Load the ONNX file
model = onnx.load('../model_simple.onnx')

# Import the ONNX model to Tensorflow
tf_rep = prepare(model)

# Input nodes to the model
print('inputs:', tf_rep.inputs)

# Output nodes from the model
print('outputs:', tf_rep.outputs)

# All nodes in the model
print('tensor_dict:')
print(tf_rep.tensor_dict)

tf_rep.export_graph("model_transformer_slt.pb")

converter = tf.lite.TFLiteConverter.from_frozen_graph(
        "model_transformer_slt.pb", tf_rep.inputs, tf_rep.outputs)
tflite_model = converter.convert()
open("model_transformer_slt.tflite", "wb").write(tflite_model)