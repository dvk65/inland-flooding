# import libraries
from utils import stn_utils
import time

# track the runtime
start = time.time()

print('STN FLOOD EVENT DATA COLLECTION AND PREPROCESSING')

# set variables
new_england_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude']
duplicate_check = ['event', 'latitude', 'longitude']

# collect high water mark data from STN database
stn_raw = stn_utils.stn_data_collect(new_england_list)

# preprocess high water mark data from STN database
stn_mod = stn_utils.stn_data_prep(stn_raw, attr_list, duplicate_check)

# calculate the runtime
end = time.time()
print(f'\nrun time: {round((end - start) / 60, 2)} minutes')



