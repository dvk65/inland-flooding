"""
This script is used to collect and preprocess flood event observations (high-water marks) 
documented in STN Flood Event Data Portal(https://stn.wim.usgs.gov/STNDataPortal/).

This script includes the following steps:
    * step 1 - download high-water marks from STN Flood Event Data Portal.
    * step 2 - preprocess the collected high-water marks.
"""

# import libraries
import time
from utils import stn_utils

# track the runtime
start = time.time()

print('\nSTART - STN FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# set variables
area_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note']
check_list = ['event', 'latitude', 'longitude']
date_threshold = 2015

stn_raw_file = 'df_stn_raw'
stn_mod_file = 'df_stn_mod'

# step 1 - collect high-water marks from STN database
stn_raw = stn_utils.collect_stn(area_list, stn_raw_file)

# step 2 - preprocess high-water marks
stn_mod = stn_utils.preprocess_stn(stn_raw, attr_list, check_list, date_threshold, stn_mod_file)

print('\nCOMPLETE - STN FLOOD EVENT DATA COLLECTION AND PREPROCESSING')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')



