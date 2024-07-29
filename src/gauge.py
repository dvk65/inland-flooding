"""
This script collects and preprocess flood events (high water levels above moderate flood stage) 
documented in USGS Water Data Service.

This script includes the following steps:
    * step 1 - collect and preprocess gauge list from NOAA.
    * step 2 - retrieve the USGSID and flood-related information for the collected gauges.
    * step 3 - collect high water level data (water level above moderate flood stage) for the gauges using their USGSIDs.
    * step 4 - preprocess the collected high water level data (water level above moderate flood stage).
"""

# import libraries
import time
from utils import gauge_utils

# track the runtime
start = time.time()

print('\nSTART - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# set variables
new_england_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'event_day', 'state', 'county', 'latitude', 'longitude', 'note']
duplicate_check = ['event_day', 'latitude', 'longitude']

# step 1 - collect and preprocess gauge list from NOAA (NWSLI and description)
df_gauge_list = gauge_utils.collect_gauge_list(new_england_list)

# step 2 - retrieve the USGSID and flood-related information for the collected gauges using NWSLI
df_gauge_info = gauge_utils.collect_gauge_info(df_gauge_list)

# step 3 - collect high water level data (water level above moderate flood stage) for the gauges using their USGSIDs 
df_gauge_raw = gauge_utils.collect_water_level(df_gauge_info)

# step 4 - preprocess the collected high water level data (water level above moderate flood stage).
df_gauge_mod = gauge_utils.preprocess_water_level(df_gauge_raw, attr_list, duplicate_check)

print('\nCOMPLETE - GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')