#!/usr/bin/env python
# coding: utf-8

# In[20]:


import os
import json
import subprocess

config_path = '/mnt/vdofilesystem/count_people_engine/config/'
input_path = '/mnt/vdofilesystem/count_people_engine/input_vdo/'
gt_path = '/mnt/vdofilesystem/count_people_engine/sukishi_gt_sheets'
mp_path = '/mnt/vdofilesystem/count_people_engine/mp_output/'

files = os.listdir(input_path)
config_file = os.listdir(config_path)
input_list = [i.split('.')[0] for i in files if i.endswith('.json')]
config_list = [c for c in config_file if c.endswith('.json')]

for i in range(config_list):
    for vdo in input_list:
        cmd_cout_people = "python count_people.py" + " --config_path "+config_path+config_list[i]+" --input "+input_path+vdo+" --mp_path"+mp_path
        subprocess.run([cmd_cout_people], shell=True, executable='/bin/bash')
        
    F1_calc = "python F1_count_people.py" + " --gt "+gt_path+" --mp "+ mp_path[i]
    subprocess.run([F1_calc], shell=True, executable='/bin/bash')



