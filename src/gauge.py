"""
This script collects and preprocess flood event observations (high-water levels - above moderate flood stage) 
stored in USGS Water Data Service.

This script includes the following steps:
    * step 1 - collect and preprocess gauge list with `nswli` identifier from NOAA;
    * step 2 - collect and preprocess usgsid and flood-related information for the collected gauges;
    * step 3 - collect high-water levels (water level above moderate flood stage) for the gauges using their usgsids;
    * step 4 - preprocess the collected high-water levels.
"""

# import libraries
import time
from utils import gauge_utils, global_utils
import pandas as pd

# track the runtime
start = time.time()

print('\nSTART - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# set variables
area_list = ["CT", "ME", "MA", "NH", "RI", "VT"] # two-letter state abbreviation list (New England Region)
attr_list = ['id', 'event', 'event_day', 'state', 'county', 'latitude', 'longitude', 'note'] # attributes selected for this project 
date_threshold = '2017-03-28' # date used to select the flood event observations (Sentinel-2 availability)

# set filenames to save datasets to CSV files
gauge_list_file = 'df_gauge_list' 
gauge_info_file = 'df_gauge_info'
gauge_raw_file = 'df_gauge_raw'
gauge_mod_file = 'df_gauge_mod'

# step 1 - collect and preprocess gauge list from NOAA (nwsli and description)
df_gauge_list = gauge_utils.collect_gauge_list(area_list, gauge_list_file)

# step 2 - collect and preprocess usgsid and flood-related information for the collected gauges using nwsli
df_gauge_info = gauge_utils.collect_gauge_info(df_gauge_list, gauge_info_file)

# step 3 - collect high-water levels (water level above moderate flood stage) for the gauges using their usgsids 
# df_gauge_info = pd.read_csv('data/df_gauge/df_gauge_info.csv', dtype=object) # dtype=object necessary if using the saved CSV file
df_gauge_raw = pd.DataFrame()

# split the df_gauge_info into 6 parts based on the states in area_list to avoid MaxRetryError
for i in area_list:
    df_i = df_gauge_info[df_gauge_info['state'] == i].reset_index(drop=True)
    df_gauge_raw_i = gauge_utils.collect_water_level(df_i, date_threshold, f'{gauge_raw_file}_{i}', i)
    df_gauge_raw = pd.concat([df_gauge_raw, df_gauge_raw_i], ignore_index=True)
    time.sleep(10) # sleep for 10 seconds to avoid hitting the server too frequently

df_gauge_raw['id'] = df_gauge_raw['nwsli'] + '_' + df_gauge_raw.index.astype(str) # assign id to each data point
global_utils.describe_df(df_gauge_raw, 'gauge high-water levels')
df_gauge_raw.to_csv(f'data/df_gauge/{gauge_raw_file}.csv', index=False)

# step 4 - preprocess the collected high-water levels (water level above moderate flood stage).
df_gauge_mod = gauge_utils.preprocess_water_level(df_gauge_raw, attr_list, gauge_mod_file)

print('\nCOMPLETE - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')