#!/usr/bin/env python
# coding: utf-8

# In[20]:


import os
import json
import subprocess
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--config", required=False, help='write specific config file')
ap.add_argument("--allconfig", required=False, help='write specific config file')
# ap.add_argument("--sconfig", required=True, help='write start config file')
# ap.add_argument("--econfig", required=True, help='write end config file')
options = ap.parse_args()

args = vars(ap.parse_args())
c = args['config']
# sc = args['sconfig']
# ec = args['econfig']

config_path = '/media/B6825AA1825A6641/count_people_engine/config/'
input_path = '/media/B6825AA1825A6641/count_people_engine/input_vdo/'
gt_path = '/media/B6825AA1825A6641/count_people_engine/sukishi_gt_sheets.xlsx'
mp_path = '/media/B6825AA1825A6641/count_people_engine/mp_output/'

files = os.listdir(input_path)
config_file = os.listdir(config_path)
mp_file = os.listdir(mp_path)
input_list = [i.split('.')[0] for i in files if i.endswith('.json')]
config_list = [c for c in config_file if c.endswith('.json')]
mp_list = [m for m in mp_file if m.endswith('.xlsx')]
print('length of mp files in folder:')
print(len(mp_list))

def use_config(cfile):
    j=0
    for vdo in input_list:
        print('running video', j)
        cmd_cout_people = "python count_people.py" + " --config_path "+config_path+cfile+" --input "+input_path+vdo+" --mp "+mp_path
        subprocess.run([cmd_cout_people], shell=True, executable='/bin/bash')
        j = j+1

    



if options.allconfig:
    for i in range(len(config_list)):
        cfile = config_list[i]
        use_config(cfile)
        mp_file = os.listdir(mp_path)
        mp_list = [m for m in mp_file if m.endswith('.xlsx')]
        F1_calc = "python F1_count_people.py" + " --gt "+gt_path+" --mp "+ mp_list[i]
        subprocess.run([F1_calc], shell=True, executable='/bin/bash')
    

elif options.config:
    cfile = 'config_v'+c+'.json'
    use_config(cfile)
    F1_calc = "python F1_count_people.py" + " --gt "+gt_path+" --mp "+ "sukishi_mp_sheets_config_v"+c+".xlsx"
    subprocess.run([F1_calc], shell=True, executable='/bin/bash')
    



