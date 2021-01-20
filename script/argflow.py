import tensorflow as tf
from tensorflow.keras.layers import *
from tensorflow.keras import Model
from tensorflow.keras import backend as K
import numpy as np
import os
import argparse
import warnings
import json
 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description='run DeepTrio for PPI prediction')
parser.add_argument('-p1', '--protein1', required=True, type=str, help='configuration of the first protein group in fasta format with path, which can contain multiply sequences')
parser.add_argument('-p2', '--protein2', required=True, type=str, help='configuration of the second protein group in fasta format with path, whcih can contain multiply sequences')
parser.add_argument('-m', '--model', default='human', required=True, type=str, help='configuration of the deep learning model: human, yeast or general')
parser.add_argument('-o', '--output', default='default', type=str, help='configuration of the name of output without a filename extension')

static_args = parser.parse_args()

error_report = 0

file_1_path = './' + static_args.protein1
file_2_path = './' + static_args.protein2
file_output = static_args.output + '.txt'

if static_args.model == 'human':
    model_path = './DeepTriplet_acc_full.h5'
elif static_args.model == 'yeast':
    model_path = './DeepTriplet_acc_full.h5'
else:
    model_path = './DeepTriplet_acc_full.h5'


if static_args.model in ['human','yeast','general']:
    pass
else:
    error_report = 1
print ('Welcome to use our sortware')
def read_file(file_path):
    namespace = {}
    with open(file_path, 'r') as r:
        line = r.readline()
        while line != '':
            if line.startswith('>'):
                name = line.strip()
                namespace[name] = ''
                line = r.readline()
            else:
                namespace[name] += line.strip().upper()
                line = r.readline()
    return namespace

p1_group = read_file(file_1_path)
p2_group = read_file(file_2_path)

p1_name_list = list(p1_group.keys())
p2_name_list = list(p2_group.keys())
        
def to_arr(seq):
    amino_acid ={'A':1,'C':2,'D':3,'E':4,'F':5,
                 'G':6,'H':7,'I':8,'K':9,'L':10,
                 'M':11,'N':12,'P':13,'Q':14,'R':15,'S':16,
                 'T':17,'V':18,'W':19,'Y':20,'U':21,'X':22,'B':0}

    length = len(seq)
    a1 = np.zeros([length,], dtype = int)
    k = 0
    for AA in seq:
        a1[k] = amino_acid[AA]
        k += 1
    return a1

def pad_arr(arr):
    arr=np.pad(arr,(0,1500-len(arr)))
    return arr


def convert_numerical_list(name_list, protein_group):
    seq_list = []
    for name in name_list:
        seq = to_arr(protein_group[name])
        seq = pad_arr(seq)
        seq_list.append(seq)
    return seq_list
        
p1_seq_list = convert_numerical_list(p1_name_list, p1_group)
p2_seq_list = convert_numerical_list(p2_name_list, p2_group)

group_seq_1 = []
group_seq_2 = []

group_name = []

for n1 in range(len(p1_name_list)):
    for n2 in range(len(p2_name_list)):
        group_seq_1.append(p1_seq_list[n1])
        group_seq_2.append(p2_seq_list[n2])
        group_name.append(p1_name_list[n1] + '\t' + p2_name_list[n2])

group_arr_1 =  np.array(group_seq_1)
group_arr_2 =  np.array(group_seq_2)

# print(group_arr_1)
# print(group_arr_2)
# print(group_arr_1.shape)
# print(group_arr_2.shape)
# print(group_name)

class MyMaskCompute(Layer):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
            
    def call(self, inputs, mask):
        #mask = inputs._keras_mask
        mask = K.cast(mask, K.floatx())
        mask = tf.expand_dims(mask,-1)
        x = inputs * mask
        return x
    
    def compute_mask(self, inputs, mask=None):
        return None

class MySpatialDropout1D(Dropout):

    def __init__(self, rate, **kwargs):
        super(MySpatialDropout1D, self).__init__(rate, **kwargs)
        self.input_spec = InputSpec(ndim=3)

    def _get_noise_shape(self, inputs):
        input_shape = K.shape(inputs)
        noise_shape = (input_shape[0], input_shape[1], 1)
        return noise_shape
print('Model loading')
model = tf.keras.models.load_model(model_path, custom_objects={'MyMaskCompute':MyMaskCompute, 'MySpatialDropout1D':MySpatialDropout1D})

predictions_test = model.predict([group_arr_1, group_arr_2])

print(predictions_test)

# with open(file_output, 'w') as w:
#     for n1 in range(len(predictions_test)):
#         w.write(group_name[n1])
#         for n2 in range(len(predictions_test[n1])):
#             w.write('\t' + str(predictions_test[n1][n2]))
#         w.write('\n')

# output_data = {}
# for n in range(len(predictions_test)):
#     output_data[group_name[n]] = {}
#     output_data[group_name[n]]['model'] = static_args.model
#     output_data[group_name[n]]['probability'] = str(predictions_test[n][0])
#     if predictions_test[n][0] >= 0.5:
#         output_data[group_name[n]]['result'] = 'binding'
#     elif predictions_test[n][2] >= 0.5:
#         output_data[group_name[n]]['result'] = 'single-protein'
#     else:
#         output_data[group_name[n]]['result'] = 'non-binding'

output_data = []
tmp = []
for n in range(len(predictions_test)):
    protein_names = group_name[n].split('\t')
    tmp.append(protein_names[0])
    tmp.append(protein_names[1])
    tmp.append(static_args.model)
    tmp.append(str(predictions_test[n][0]))
    if predictions_test[n][0] >= 0.5:
        tmp.append('binding')
    elif predictions_test[n][2] >= 0.5:
        tmp.append('single-protein')
    else:
        tmp.append('non-binding')
    output_data.append(tmp)
    tmp = []

with open(file_output, 'w') as w:
    json.dump(output_data, w)

print('Thank you for using')