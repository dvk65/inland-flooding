"""
This script analyze the collected Sentinel 2 images.

This script includes the following steps:
    * step 1 - authenticate.
    * step 2 - collect Sentinel 2 images.
"""
# import libraries
import ee
import time
import pandas as pd
from utils import sentinel2_utils


# track the runtime
start = time.time()

# step 1 - trigger the authentication flow
ee.Authenticate()
ee.Initialize(project='inundation')

# set variables
buffer_dis = 6000
overlap_threshold = 20
pixel_threshold = 1.0

# load flood event data
df = pd.read_csv('data/flood_events.csv')

# step 2 - collect the corresponding sentinel imagery
sentinel2_utils.collect_sentinel2_by_event(df, buffer_dis, overlap_threshold, pixel_threshold, 10)

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')