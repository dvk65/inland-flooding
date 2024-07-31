"""
This script runs the analysis for the collected Sentinel 2 images and identifies the ideal dataset for the KMeans clustering algorithm. 

This file contains the following steps:
    * step 1 - create a dataframe to store and organize the image information.
    * step 2 - plot the collect images for visual inspection.
    * step 3 - clean the dataset to extract the ideal image datasets for KMeans clustering
    * step 4 - plot all filtered images organized by ids
    * step 5 - drop the unwanted instances
"""

# import libraries
import pandas as pd
from utils import eda_s2_utils

# load the dataset
df = pd.read_csv('data/flood_event.csv')
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# step 1 - delete empty folders
eda_s2_utils.check_s2_folder(df)

# step 2 - create a dataframe to store the image filename and its metadata
df_s2 = eda_s2_utils.create_s2_df(df)

# step 3 - add necessary info to df_s2 
attr_list = ['id', 'state', 'county', 'latitude', 'longitude', 'note', 'category', 'event_day']
df_s2_mod = eda_s2_utils.add_metadata_flood_event(df, df_s2, attr_list)

# step 4 - filter df_s2
df_s2_filtered = eda_s2_utils.filter_df_s2(df_s2_mod)

# step 5 - plot the images to identify the ideal events and dates
eda_s2_utils.plot_satellite(df_s2_filtered)

# step 6 - drop images based on step 5
df_selected = eda_s2_utils.filter_satellite(df_s2_filtered)