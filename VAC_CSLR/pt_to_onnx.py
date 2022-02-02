from torch.autograd import Variable

import torch.nn as nn
import torch.onnx
import torchvision
import torch
from main import import_class
import numpy as np
import utils
from collections import OrderedDict

def modified_weights(state_dict, modified=False):
    state_dict = OrderedDict([(k.replace('.module', ''), v) for k, v in state_dict.items()])
    if not modified:
        return state_dict
    modified_dict = dict()
    return modified_dict

device = utils.GpuDataParallel()
device.set_device('None')
model_args = {"num_classes": 1296, "c2d_type": "resnet18", "conv_type": 2, "use_bn": 1}
loss_weights = {"ConvCTC": 1.0, "SeqCTC": 1.0, "Dist": 10.0}
gloss_dict = np.load('/home/aayush/Thesis/VAC_CSLR/preprocess/phoenix2014/gloss_dict.npy', allow_pickle=True).item()

model_name = 'resnet18_slr_pretrained_distill25.pt'
state_dict = torch.load(model_name, map_location=torch.device('cpu'))

model_class = import_class("slr_network.SLRModel")
model = model_class(**model_args, gloss_dict=gloss_dict,
                    loss_weights=loss_weights)

weights = modified_weights(state_dict['model_state_dict'], False)
model.load_state_dict(weights, strict=True)
print(model)
model.eval()

'''
checkpoint['model']['generator.0.weight'] = checkpoint['generator']['0.weight']
checkpoint['model']['generator.0.bias'] = checkpoint['generator']['0.bias']

model.load_state_dict(checkpoint['model'])
print('################$$$$$$$$$$')
# print(model)
'''

dummy_input = torch.randint(100,
                            (2, 184, 3, 224, 224))
#dummy_list = [216, 112]
dummy_list = torch.Tensor([184, 148])

#dummy_input1 = torch.randint(16,
#                             (29, 71, 1))  # dummy_input = torch.from_numpy(X_test[0].reshape(1, -1)).float().to(device)
#dummy_input2 = torch.randint(16, (71,))

# Export to ONNX format
torch.onnx.export(model, (dummy_input, dummy_list), 'model_simple.onnx', verbose=True)