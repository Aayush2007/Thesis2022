from torch.autograd import Variable

import torch.nn as nn
import torch.onnx
import torchvision
import torch
from onmt.model_builder import build_base_model
from onmt.utils.parse import ArgumentParser
import onnx
from onnx_tf.backend import prepare
import tensorflow as tf

checkpoint = torch.load('model_step_1600.pt')

model_opt = ArgumentParser.ckpt_model_opts(checkpoint['opt'])
ArgumentParser.update_model_opts(model_opt)
ArgumentParser.validate_model_opts(model_opt)
vocab = checkpoint['vocab']
fields = vocab

model = build_base_model(model_opt, fields, None, checkpoint)
model.eval()

'''
checkpoint['model']['generator.0.weight'] = checkpoint['generator']['0.weight']
checkpoint['model']['generator.0.bias'] = checkpoint['generator']['0.bias']

model.load_state_dict(checkpoint['model'])
print('################$$$$$$$$$$')
# print(model)
'''

dummy_input = torch.randint(16,
                            (15, 71, 1))
dummy_input1 = torch.randint(16,
                             (29, 71, 1))  # dummy_input = torch.from_numpy(X_test[0].reshape(1, -1)).float().to(device)
dummy_input2 = torch.randint(16, (71,))

# Export to ONNX format
torch.onnx.export(model, (dummy_input, dummy_input1, dummy_input2), 'model_simple_12.onnx', verbose=True, opset_version=14)

