"""
This script collects and preprocess flood events (high water marks) documented in STN Data Portal.

This script includes the following steps:
    * step 1 - download high water marks from STN Data Portal.
    * step 2 - preprocess the collected high water mark data.
"""

# import libraries
import time
from utils import stn_utils

# track the runtime
start = time.time()

print('\nSTART - STN FLOOD EVENT DATA COLLECTION AND PREPROCESSING\n')

# set variables
new_england_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note']
duplicate_check = ['event', 'latitude', 'longitude']

# step 1 - collect high water mark data from STN database
stn_raw = stn_utils.collect_stn(new_england_list)

# step 2 - preprocess high water mark data 
stn_mod = stn_utils.preprocess_stn(stn_raw, attr_list, duplicate_check)

print('\nCOMPLETE - STN FLOOD EVENT DATA COLLECTION AND PREPROCESSING')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')



