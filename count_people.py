#!/usr/bin/env python
# coding: utf-8

# In[9]:


import time
import numpy as np
import argparse
from tqdm import tqdm
import datetime
import math
import os.path
import json
import cv2
import pandas as pd
import csv
from openpyxl import load_workbook


# In[10]:


def initial_parts_dict():
    parts_dict = {'Nose' : 0, 
                  'LEye' : 1,
                  'REye' : 2,
                  'LEar' : 3,
                  'REar' : 4,
                  'LShoulder' : 5,
                  'RShoulder' : 6,
                  'LElbow' : 7,
                  'RElbow' : 8,
                  'LWrist' : 9,
                  'RWrist' : 10 ,
                  'LHip' : 11,
                  'RHip' : 12,    
                  'LKnee' : 13,
                  'RKnee' : 14,
                  'LAnkle' : 15,
                  'RAnkle' : 16}
    return parts_dict


# In[11]:


def draw_zone(config_path):
    with open(config_path, encoding='utf-8') as F:
        json_data = json.loads(F.read())
        outer_polygon = json_data["outer_polygon"]
        inner_polygon = json_data["inner_polygon"]
        
        outer_polygon = list(map(eval, outer_polygon)) 
        inner_polygon = list(map(eval, inner_polygon))
    return(outer_polygon,inner_polygon)


# In[12]:


def direction(a, b, c):
    val = (b[1]-a[1])*(c[0]-b[0])-(b[0]-a[0])*(c[1]-b[1])
    if val == 0:
        return 0
    elif val < 0:
        return -1
    else:
        return 1


# In[13]:


def isIntersect(part_point1, part_point2, detect_point1, detect_point2):
    dir1 = direction(part_point1, part_point2, detect_point1)
    dir2 = direction(part_point1, part_point2, detect_point2)
    dir3 = direction(detect_point1, detect_point2, part_point1)
    dir4 = direction(detect_point1, detect_point2, part_point2)
    
    if(dir1*dir2*dir3*dir4 == 0):
        return False
    elif(dir1 != dir2 and dir3 != dir4):
        return True
    else:
        return False


# In[14]:


def zone_detection(skeleton_keypoint, detect_polygon, parts_dict, config_path):
    score = 0
    
    with open(config_path, encoding='utf-8') as F:
        json_data = json.loads(F.read())
    
    point_detect_list = json_data["point_detect_list"]
    target_score = json_data["target_score"]

    for i in range (len(point_detect_list)):
        count = 0
        for j in range (len(detect_polygon)-1):
            if(isIntersect((0,0), (skeleton_keypoint[3*parts_dict[point_detect_list[i]]], skeleton_keypoint[3*parts_dict[point_detect_list[i]]+1]), detect_polygon[j] , detect_polygon[j+1])):
                count+=1
        if(isIntersect((0,0), (skeleton_keypoint[3*parts_dict[point_detect_list[i]]], skeleton_keypoint[3*parts_dict[point_detect_list[i]]+1]), detect_polygon[0] , detect_polygon[-1])):
            count+=1
        if(count%2 == 1 and skeleton_keypoint[3*parts_dict[point_detect_list[i]]+2] >= 0.15):
            score+=1
    if score >= target_score:
        return True #all parts in point_detect_list are in the polygon
    else:
        return False


# In[15]:


def count_detect(config_path,img_dir,json_file,video_name,mp_path):
    config_name = os.path.basename(config_path)
    with open(config_path, encoding='utf-8') as FConfig:
        config = json.loads(FConfig.read())
    
    store = config["store"]
    
    video = video_name
    json_f = json_file
    image = img_dir
    
    with open(json_f, encoding='utf-8') as F:
        json_data = json.loads(F.read())
    
    #init data
    count_in = 0
    count_out = 0
    count_pass = 0
    not_defind = 0
    outer_polygon,inner_polygon = draw_zone(config_path)
    parts_dict = initial_parts_dict()
    key_list = list(json_data.keys())
    file_list = [fl for fl in os.listdir(image)]
    file_list.sort()
    key_list.sort()
    idx_list = []
    in_idx = []
    out_idx= []
    idx_inout = dict()
    
    ### init write excel ###
    inout_fieldnames = ['idx', 'frame_no', 'date', 'timestamp' , 'in/out/pass']
    info_fieldnames = ['Info', 'Detail']
    report_fieldnames = ['vdo_name', 'frame', 'idx']
    inout_writer = pd.DataFrame(columns = inout_fieldnames)
    inout_info = pd.DataFrame(columns = info_fieldnames)
    report_result = pd.DataFrame(columns = report_fieldnames)

    for i in tqdm(key_list):
        if i in file_list:
            frame_index = file_list.index(i)
            frame_no = file_list[frame_index].split('_')[0]

            Time_str = '00:00:00'
            image = json_data[i]
            image_len = len(image)

            for k in range (image_len):
                if ('idx' not in image[k]):
                    continue

                current_keypoint = image[k]['keypoints']
                idx = image[k]['idx']

                if idx not in idx_list:
                    idx_list.append(idx)

                idx_inout[(frame_no, idx)] = {'idx_check' : 0, 'frame_check' : 0,'counted' : 0, 'frame_id' : i, 'idx': idx ,'time' : Time_str}

                #check skeleton zone
                out_detected = zone_detection(current_keypoint, outer_polygon, parts_dict, config_path)      
                in_detected = zone_detection(current_keypoint, inner_polygon, parts_dict, config_path)

                if out_detected:
                    idx_inout[(frame_no, idx)]['counted'] = -1

                if in_detected:
                    idx_inout[(frame_no, idx)]['counted'] = 1

    offset = 10
    for idxl in idx_list :
        frame_idx = []  
        for item in idx_inout:
            if idx_inout[item]['idx'] == idxl:
                frame_idx.append(idx_inout[item])
        for i in range(len(frame_idx)-1):
            #walk in condition 
            if frame_idx[i]['counted'] == -1 and frame_idx[i+1]['counted'] == 1:
                start = i+1
                end_pos = start+offset 
                end_neg = start-offset 
                #check bound
                if start >= len(frame_idx) or end_pos >= len(frame_idx) or end_neg >= len(frame_idx):
                    start = len(frame_idx)-1
                    end_pos = len(frame_idx)-1 
                    end_neg = len(frame_idx)-1 
                if start < 0 or end_pos< 0 or end_neg < 0:
                    start = 0
                    end_pos = 0 
                    end_neg = 0 

                if sum(frame_idx[start]['counted'] for start in range (start,end_pos)) == offset and abs(sum(frame_idx[start]['counted'] for start in range (end_neg,start))) == offset:
                    frame_idx[i]['idx_check'] = 1

                if (sum(abs(int(frame_idx[start]['frame_id'][3:9]) - int(frame_idx[start+1]['frame_id'][3:9])) for start in range (start,end_pos))) == offset and sum(abs(int(frame_idx[start]['frame_id'][3:9]) - int(frame_idx[start+1]['frame_id'][3:9])) for start in range (end_neg,start)) == offset:
                    frame_idx[i]['frame_check'] = 1   

            #walk out condition 
            if frame_idx[i]['counted'] == 1 and frame_idx[i+1]['counted'] == -1:
                start = i+1
                end_pos = start+offset 
                end_neg = start-offset 
                #check bound
                if start >= len(frame_idx) or end_pos >= len(frame_idx) or end_neg >= len(frame_idx):
                    start = len(frame_idx)-1
                    end_pos = len(frame_idx)-1 
                    end_neg = len(frame_idx)-1
                if start < 0 or end_pos< 0 or end_neg < 0:
                    start = 0
                    end_pos = 0 
                    end_neg = 0 

                #check counted offset
                if abs(sum(frame_idx[start]['counted'] for start in range (start,end_pos))) == offset and sum(frame_idx[start]['counted'] for start in range (end_neg,start)) == offset:
                    frame_idx[i]['idx_check'] = -1

                #check frame offset

                if (sum(abs(int(frame_idx[start]['frame_id'][3:9]) - int(frame_idx[start+1]['frame_id'][3:9])) for start in range (start,end_pos))) == offset and sum(abs(int(frame_idx[start]['frame_id'][3:9]) - int(frame_idx[start+1]['frame_id'][3:9])) for start in range (end_neg,start)) == offset:
                    frame_idx[i]['frame_check'] = -1   
        
    for current in tqdm(idx_inout):
        if(idx_inout[current]['idx_check'] == 1 and idx_inout[current]['frame_check'] == 1): 
            print("walk_in")
            print(idx_inout[current]['frame_id'], idx_inout[current]['idx'])
            count_in += 1
            inout_writer = inout_writer.append({'idx': idx_inout[current]['idx'], 'frame_no':idx_inout[current]['frame_id'], 'date': '00:00:00', 'timestamp': '00:00:00', 'in/out/pass': 'in'}, ignore_index=True)
            frame_int = int(idx_inout[current]['frame_id'][3:9])
            report_result = report_result.append({'vdo_name': video, 'frame': frame_int, 'idx': idx_inout[current]['idx']}, ignore_index=True)
        if(idx_inout[current]['idx_check'] == -1 and idx_inout[current]['frame_check'] == -1): 
            print("walk_out")
            print(idx_inout[current]['frame_id'], idx_inout[current]['idx'])
            count_out += 1 
            inout_writer = inout_writer.append({'idx': idx_inout[current]['idx'], 'frame_no':idx_inout[current]['frame_id'], 'date': '00:00:00', 'timestamp': '00:00:00', 'in/out/pass': 'out'}, ignore_index=True)
#             report_result = report_result.append({'Video file name':video, 'Frame name':idx_inout[current]['frame_id'], 'idx':idx_inout[current]['idx']}, ignore_index=True)          


    ### write excel ###
    inout_info = inout_info.append({'Info': 'Customer Code', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Customer Name', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Store Code', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Store Name', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Camera Code', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Video Filename', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Process Date', 'Detail': 'test'}, ignore_index=True)
    inout_info = inout_info.append({'Info': 'Output Type', 'Detail': 'CustomerVisiting'}, ignore_index=True)
    
       
    if not os.path.isfile(mp_path +'\\'+'sukishi_mp_sheets_'+config_name+'.xlsx'):
        writer_report = pd.ExcelWriter(mp_path +'\\'+'sukishi_mp_sheets_'+config_name+'.xlsx', engine = 'xlsxwriter')
        report_result['person_walkin'] = count_in
        sh_name = video.split('.')[0]
        report_result.to_excel(writer_report, sheet_name= sh_name, index=False)
        writer_report.save()  
    else:
        workbook = load_workbook(mp_path +'\\'+'sukishi_mp_sheets_'+config_name+'.xlsx')
        writer_report = pd.ExcelWriter(mp_path +'\\'+'sukishi_mp_sheets_'+config_name+'.xlsx', engine = 'openpyxl')
        writer_report.book = workbook
        report_result['person_walkin'] = count_in
        sh_name = video.split('.')[0]
        report_result.to_excel(writer_report, sheet_name= sh_name, index=False)
        writer_report.save()  

    return (count_in, count_out, count_pass,not_defind)


# In[16]:


if __name__ == "__main__":
    start = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--config_path", required=True, help="path of json file")
    ap.add_argument("--input", required=True , help="path of existing counting file")
 
    args = vars(ap.parse_args())
    config_path = args['config_path']
    mp_path = args['mp_path']
    
    input_file = args['input']
    
    img_dir = input_file+"_img"
    json_file = input_file+".json"
    video_name = input_file
    
    print(count_detect(config_path,img_dir,json_file,video_name,mp_path))
    end = time.time()
    print(end - start)






