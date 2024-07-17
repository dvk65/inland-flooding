# collect sentinel 2 imagery by flood event
import pandas as pd
from utils import satellite_utils
import ee
import os

import time

# track the runtime
start = time.time()

ee.Authenticate()
ee.Initialize(project='inundation')

# parameters
buffer_dis = 6000
overlap_threshold = 20
pixel_threshold = 1.0

# load STN flood event data
stn = pd.read_csv('data/stn/stn_flood_event_mod.csv')

# collect the corresponding sentinel imagery - STN flood event
date_range = {'2021 Henri': ['2021-07-31', '2021-09-08'],
              '2018 March Extratropical Cyclone': ['2018-02-14', '2018-03-19'],
              '2018 January Extratropical Cyclone': ['2017-12-18', '2018-01-22'],
              '2023 July MA NY VT Flood': ['2023-06-25', '2023-07-27'],
              '2023 December East Coast Cyclone': ['2023-12-02', '2024-01-04']}
satellite_utils.collect_sentinel2_by_event(stn, 600, buffer_dis, overlap_threshold, pixel_threshold, 'sentinel2', 10, date_range)

# calculate the runtime
end = time.time()
print(f'\nrun time: {round((end - start) / 60, 2)} minutes')