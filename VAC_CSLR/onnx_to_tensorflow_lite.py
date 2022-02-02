import sys
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import onnx
import tensorflow as tf
from onnx_tf.backend import prepare

# Load the ONNX file
model = onnx.load('model_simple_14.onnx')

# Check that the IR is well formed
onnx.checker.check_model(model)

# Print a Human readable representation of the graph
onnx.helper.printable_graph(model.graph)

# Import the ONNX model to Tensorflow
tf_rep = prepare(model)
print(tf_rep)
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
