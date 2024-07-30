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
from utils import s2_utils, global_utils


# track the runtime
start = time.time()

# step 1 - trigger the authentication flow
ee.Authenticate()
ee.Initialize(project='inundation')

# set variables
buffer_dis = 6000
overlap_threshold = 20
pixel_threshold = 1.0
flood_event_periods = {'2021 Henri': ['2021-08-15', '2021-08-23'],
              '2018 March Extratropical Cyclone': ['2018-03-01', '2018-03-05'],
              '2018 January Extratropical Cyclone': ['2018-01-02', '2018-01-06'],
              '2023 July MA NY VT Flood': ['2023-07-10', '2023-07-11'],
              '2023 December East Coast Cyclone': ['2023-12-17', '2023-12-18']}

# load STN high-water mark data
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# add start_day/end_day and combine two datasets
global_utils.print_func_header('add the formed and dissipated dates for the events')
stn[['formed', 'dissipated']] = stn['event'].apply(lambda x: s2_utils.map_dates(x, flood_event_periods))
stn['start_day'] = pd.to_datetime(stn['formed']) - pd.Timedelta(days=20)
stn['end_day'] = pd.to_datetime(stn['dissipated']) + pd.Timedelta(days=20)

gauge['start_day'] = pd.to_datetime(gauge['event_day']) - pd.Timedelta(days=20)
gauge['end_day'] = pd.to_datetime(gauge['event_day']) + pd.Timedelta(days=20)
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note', 'start_day', 'end_day']
df = pd.concat([stn[attr_list], gauge[attr_list]])

# step 2 - collect the corresponding sentinel imagery (STN and Gauge combined)
s2_utils.collect_sentinel2_by_event(df, buffer_dis, overlap_threshold, pixel_threshold, 10)

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')