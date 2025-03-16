"""
This script runs the analysis for the collected Sentinel 2 images and identifies the ideal dataset for the KMeans clustering algorithm. 

This file contains the following steps:
    * step 1 - delete empty folders;
    * step 2 - create a dataframe to store the image filename and its metadata;
    * step 3 - add necessary info to df_s2;
    * step 4 - plot the images to identify the ideal events and verify the assigned period labels;
    * step 5 - drop images based on step 4;
    * step 6 - extract images where their ids have a during flood period label.
    * step 7 - plot the distribution;
    * step 8 - explore ndwi threshold;
    * step 9 - collect the National Hydrography Dataset for specified states and plot all data one by one (Sentinel-2 image, flowline, NDWI, cloud).
"""

# import libraries
import time
import pandas as pd
from utils import eda_s2_utils, global_utils, eda_flood_event_utils

# track the runtime
start = time.time()
print('\nSTART - NHD DATA COLLECTION AND PLOTTING\n')

# set variable
area_abbr_list = global_utils.area_abbr_list
area_list = ["ME"]

# load the dataset
df = pd.read_csv('data/flood_event_ME.csv')
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')
stn = pd.DataFrame(stn[stn['state'] == 'ME'])
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')
gauge = pd.DataFrame(gauge[gauge['state'] == 'ME'])

# step 1 - delete empty folders
eda_s2_utils.check_s2_folder(df)

# step 2 - create a dataframe to store the image filename and its metadata
df_s2 = eda_s2_utils.create_s2_df(df)

# step 3 - add necessary info to df_s2 
attr_list = ['id', 'state', 'county', 'latitude', 'longitude', 'note', 'source', 'event_day']
flood_day_adjust_dict = {'gauge': (0, 0), 'stn': (0, 0)} # can be adjusted after the 
df_s2_mod = eda_s2_utils.add_metadata_flood_event(df, df_s2, attr_list, flood_day_adjust_dict)

# step 4 - plot the images to identify the ideal data and also verify the assigned period label (it's possible to observe flooded area but assigned inaccurate lable)
eda_s2_utils.plot_s2(df_s2_mod)

# step 5 - drop images based on step 5 (two steps - select event and drop unwanted image)
selected_event = ['2018-03', '2021-05', '2020-02', '2023-12', '2020-09', '2019-09', '2021-08', '2020-03', '2024-01', '2020-10', '2019-10', '2021-09', '2020-04', '2024-03', '2020-11', '2019-11', '2022-10', '2020-05', '2024-04', '2021-03', '2019-12', '2023-05', '2020-06', '2021-04', '2020-01', '2023-08', '2020-07']
# date_drop = ['20230619', '20230701', '20230719', '20230731', '20230805'] 2021-05, 2018-03, 
date_drop = []
cloud_threshold = 50
flood_day_adjust_dict = {'gauge': (1, 1), 'stn': (0, 0)}
# eda_s2_utils.select_s2(df_s2_mod, selected_event, cloud_threshold, date_drop, flood_day_adjust_dict, explore='complete')
df_selected = eda_s2_utils.select_s2(df_s2_mod, selected_event, cloud_threshold, date_drop, flood_day_adjust_dict, explore='complete') 

# step 6 - extract images where their ids have a during flood period label (the flood event observation is captured by Sentinel-2)
flood_ids = df_selected[df_selected['period'] == 'during flood']['id'].unique()
df_id_with_flood = df_selected[df_selected['id'].isin(flood_ids)].copy()
df_id_with_flood.to_csv('data/s2_id_with_flood.csv', index=False)

# step 7 - plot the distribution 
eda_flood_event_utils.run_eda(df_id_with_flood, 'sentinel2', area_list)

# step 8 - explore ndwi threshold
threshold_list = [-0.15, -0.1, -0.05, 0.0, 0.05, 0.1]
eda_s2_utils.test_ndwi_tif(df_id_with_flood, threshold_list)

# step 9 - collect the National Hydrography Dataset for specified states and plot all data one by one (Sentinel-2 image, flowline, NDWI, cloud)
area_in_df = df_id_with_flood['state'].unique().tolist()
area_list = [state for state, abbr in area_abbr_list.items() if abbr in area_in_df]
content_selected = ['Shape/NHDFlowline.shp', 'Shape/NHDFlowline.shx', 'Shape/NHDFlowline.dbf', 'Shape/NHDFlowline.prj', 'Shape/NHDFlowlineVAA.dbf'] # selected flowline files
eda_s2_utils.download_nhd_shape(area_list, content_selected) # download flowline shapefiles 
eda_s2_utils.add_nhd_layer_s2(df_id_with_flood, area_list, area_abbr_list) # add flowline as a layer and also plot Sentinel-2 image, flowline, NDWI, and cloud

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')