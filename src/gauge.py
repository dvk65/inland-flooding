"""
This script collects and preprocess flood event observations (high-water levels - above moderate flood stage) 
documented in USGS Water Data Service.

This script includes the following steps:
    * step 1 - collect and preprocess gauge list from NOAA;
    * step 2 - collect and preprocess usgsid and flood-related information for the collected gauges;
    * step 3 - collect high-water levels (water level above moderate flood stage) for the gauges using their usgsids;
    * step 4 - preprocess the collected high-water levels.
"""

# import libraries
import time
from utils import gauge_utils
import pandas as pd

# track the runtime
start = time.time()

print('\nSTART - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# set variables
area_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'event_day', 'state', 'county', 'latitude', 'longitude', 'note']
check_list = ['event_day', 'latitude', 'longitude']
date_threshold = '2017-03-28'

gauge_list_file = 'df_gauge_list'
gauge_info_file = 'df_gauge_info'
gauge_raw_file = 'df_gauge_raw'
gauge_mod_file = 'df_gauge_mod'

# step 1 - collect and preprocess gauge list from NOAA (nwsli and description)
df_gauge_list = gauge_utils.collect_gauge_list(area_list, gauge_list_file)

# step 2 - collect and preprocess usgsid and flood-related information for the collected gauges using nwsli
df_gauge_info = gauge_utils.collect_gauge_info(df_gauge_list, gauge_info_file)

# step 3 - collect high-water levels (water level above moderate flood stage) for the gauges using their usgsids 
# df_gauge_info = pd.read_csv('data/df_gauge/df_gauge_info.csv', dtype=str)
df_gauge_raw = gauge_utils.collect_water_level(df_gauge_info, date_threshold, gauge_raw_file)

# step 4 - preprocess the collected high-water levels (water level above moderate flood stage).
df_gauge_mod = gauge_utils.preprocess_water_level(df_gauge_raw, attr_list, check_list, gauge_mod_file)

print('\nCOMPLETE - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')