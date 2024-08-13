"""
This script analyze flood-related dataframes.

This script includes the following steps:
    * step 1 - analyze the collected STN high-water mark data from STN flood event portal;
    * step 2 - analyze the collected high-water levels from USGS Water Data Service;
    * step 3 - integrate these two datasets and perform an analysis using maps.
"""

# import libraries
import time
import pandas as pd
from utils import eda_flood_event_utils

# track the runtime
start = time.time()
print('\nSTART - ANALYZE FLOOD EVENT OBSERVATIONS')

# set variables
area_list = ["CT", "ME", "MA", "NH", "RI", "VT"]

# load STN high-water mark data
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')

# step 1 - analyze the collected STN high-water mark data from STN flood event portal
eda_flood_event_utils.run_eda(stn, 'stn', area_list)

# load gauge high water level data
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# step 2 - analyze the collected high-water levels from USGS Water Data Service
eda_flood_event_utils.run_eda(gauge, 'gauge', area_list)

# combine two datasets
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note', 'source']
df = pd.concat([stn[attr_list], gauge[attr_list]])

# step 3 - integrate these two datasets and perform an analysis using maps
eda_flood_event_utils.run_eda(df, 'stn_gauge', area_list)

print('\nCOMPLETE - ANALYZE FLOOD EVENT OBSERVATIONS\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')
