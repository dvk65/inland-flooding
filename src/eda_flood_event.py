"""
This script analyze flood-related dataframes.

This script includes the following steps:
    * step 1 - analyze the collected STN high water mark data.
    * step 2 - analyze the collected high water levels from USGS Water Data Service.
    * step 3 - identify common data ranges between the two datasets and find 
               additional observations from high water levels for the flood events in STN.
"""

# import libraries
import pandas as pd
from utils import eda_flood_event_utils, global_utils

print('\nSTART - ANALYZE FLOOD EVENTS')

# set variables
area_list = ["CT", "ME", "MA", "NH", "RI", "VT"]

# load STN high-water mark data
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')

# run EDA - STN high-water marks
eda_flood_event_utils.run_eda(stn, 'stn', area_list)

# load gauge high water level data
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# run EDA - Gauge high-water levels
eda_flood_event_utils.run_eda(gauge, 'gauge', area_list)

# combine twoadd category column for STN and Gauge datasets
stn['category'] = 'stn'
gauge['category'] = 'gauge'

# # combine two datasets
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note', 'category']
df = pd.concat([stn[attr_list], gauge[attr_list]])

# run EDA - STN and Gauge on map 
eda_flood_event_utils.run_eda(df, 'stn and gauge', area_list)


