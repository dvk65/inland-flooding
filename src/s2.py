"""
This script analyze the collected Sentinel 2 images.

This script includes the following steps:
    * step 1 - run the authentication flow;
    * step 2 - prepare the flood event observation dataset;
    * step 3 - collect Sentinel 2 images.
"""
# import libraries
import ee
import time
import pandas as pd
from utils import s2_utils, global_utils

# track the runtime
start = time.time()

print('\nSTART - SENTINEL-2 IMAGERY COLLECTION\n')

# set variables
buffer_dis = 6000
overlap_threshold = 20
pixel_threshold = 1.0
flood_event_periods = global_utils.flood_event_periods

# step 1 - run the authentication flow
ee.Authenticate()
ee.Initialize(project='demoflood0803')
# load STN high-water mark data
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# step 2 - prepare the flood event observation dataset
global_utils.print_func_header('add the formed and dissipated dates for the events')
stn[['formed', 'dissipated']] = stn['event'].apply(lambda x: s2_utils.map_dates(x, flood_event_periods))
stn['start_day'] = pd.to_datetime(stn['formed']) - pd.Timedelta(days=15)
stn['end_day'] = pd.to_datetime(stn['dissipated']) + pd.Timedelta(days=16)
stn['event'] = pd.to_datetime(stn['formed']).dt.strftime('%Y-%m')
stn['event_day'] = stn.apply(lambda row: f"{row['formed']} to {row['dissipated']}", axis=1)

gauge['start_day'] = pd.to_datetime(gauge['event_day']) - pd.Timedelta(days=15)
gauge['end_day'] = pd.to_datetime(gauge['event_day']) + pd.Timedelta(days=16)

attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note', 'event_day', 'start_day', 'end_day', 'source']
df = pd.concat([stn[attr_list], gauge[attr_list]])
df.to_csv('data/flood_event.csv', index=False)

# step 3 - collect the corresponding sentinel imagery (STN and Gauge combined)
s2_utils.collect_sentinel2_by_event(df, buffer_dis, overlap_threshold, pixel_threshold, 10)

print('\nCOMPLETE - SENTINEL-2 IMAGERY COLLECTION\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')