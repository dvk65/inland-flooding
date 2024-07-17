# import libraries
from utils import gauge_utils
import time

# track the runtime
start = time.time()

print('GAUGE FLOOD EVENT DATA COLLECTION AND PREPROCESSING')

# set variables
new_england_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
attr_list = ['id', 'event', 'event_day', 'state', 'county', 'latitude', 'longitude']
duplicate_check = ['event_day', 'latitude', 'longitude']

# collect and preprocess gauge list
nwsli_list = gauge_utils.nwsli_data_collect(new_england_list)

# collect flood stage information from NOAA
flood_stage_moderate = gauge_utils.flood_stage(nwsli_list)

# collect water level above moderate flood stage from USGS water services
gauge_flood_event_raw = gauge_utils.extract_water_level(flood_stage_moderate)
gauge_flood_event_mod = gauge_utils.prep_water_level(gauge_flood_event_raw, attr_list, duplicate_check)

# calculate the runtime
end = time.time()
print(f'\nrun time: {round((end - start) / 60, 2)} minutes')