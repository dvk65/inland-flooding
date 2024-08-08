"""
This script runs the analysis for the collected Sentinel 2 images and identifies the ideal dataset for the KMeans clustering algorithm. 

This file contains the following steps:
    * step 1 - delete empty folders;
    * step 2 - create a dataframe to store the image filename and its metadata;
    * step 3 - add necessary info to df_s2;
    * step 4 - filter df_s2;
    * step 5 - plot the images to identify the ideal events and dates;
    * step 6 - drop images based on step 5;
"""

# import libraries
import os
import pandas as pd
from utils import eda_s2_utils

# set variable
area_list = ['Vermont']

# load the dataset
df = pd.read_csv('data/flood_event.csv')
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# step 1 - delete empty folders
eda_s2_utils.check_s2_folder(df)

# step 2 - create a dataframe to store the image filename and its metadata
df_s2 = eda_s2_utils.create_s2_df(df)

# step 3 - add necessary info to df_s2 
attr_list = ['id', 'state', 'county', 'latitude', 'longitude', 'note', 'source', 'event_day']
flood_day_adjust_dict = {'gauge': (0, 0), 'stn': (0, 0)}
df_s2_mod = eda_s2_utils.add_metadata_flood_event(df, df_s2, attr_list, flood_day_adjust_dict)

# step 4 - filter df_s2
df_s2_filtered = eda_s2_utils.filter_df_s2(df_s2_mod)

# step 5 - plot the images to identify the ideal events and dates
eda_s2_utils.plot_s2(df_s2_filtered)

# step 6 - drop images based on step 5 (two steps - select event and drop unwanted image)
# question - should I drop observations without image during flood or save them 
selected_event = ['2023-07']
date_drop = ['20230619', '20230701', '20230719', '20230731', '20230805']
cloud_threshold = 50
flood_day_adjust_dict = {'gauge': (1, 1), 'stn': (0, 0)}

# df_selected = eda_s2_utils.select_s2(df_s2_filtered, selected_event, cloud_threshold, date_drop) # run to explore the image for selected event
df_selected = eda_s2_utils.select_s2(df_s2_filtered, selected_event, cloud_threshold, date_drop, flood_day_adjust_dict, explore='complete') # run if both selecting event and dropping unwanted images

# explore ndwi threshold
threshold_list = [-0.1, -0.05, 0.0, 0.05, 0.1]
file_path_list = ["data/img_s2/2023-07_NDWI/44929_20230706T153819_20230706T155055_T18TXN_NDWI.tif", "data/img_s2/2023-07_NDWI/44909_20230711T153821_20230711T154201_T18TXP_NDWI.tif", "data/img_s2/2023-07_NDWI/45358_20230711T153821_20230711T154201_T18TXP_NDWI.tif"]
for i in file_path_list:
    eda_s2_utils.test_ndwi_tif(i, threshold_list)