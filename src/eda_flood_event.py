import pandas as pd
import matplotlib.pyplot as plt
from utils import eda_utils

print('\nSTN FLOOD EVENTS EDA')

# load STN flood event data
stn = pd.read_csv('data/stn/stn_flood_event_mod.csv')
eda_utils.desc_data(stn)

# Count flood events by event
eda_utils.count_by_group(stn, 'event')

# Count flood events by state
eda_utils.count_by_group(stn, 'state')

# Visualize flood event by state
eda_utils.plot_bar(stn, 'stn')

print('\nGAUGE FLOOD EVENTS EDA')

# load gauge flood event data
gauge = pd.read_csv('data/gauge/gauge_flood_event_mod.csv')
eda_utils.desc_data(gauge)

# Count flood events by event
eda_utils.count_by_group(gauge, 'event')

# Count flood events by state
eda_utils.count_by_group(gauge, 'state')

print('\nSTN Flood Event Database and Gauge Water Level Database')

# flood events possibly documented by both sources
date_stn_mod = eda_utils.convert_date(stn)
date_stn_mod_list = date_stn_mod.tolist()
date_stn_mod_list[0] = '2021-08'
gauge_select = eda_utils.check_overlap(date_stn_mod_list, gauge)

# Visualize flood event by state
eda_utils.plot_bar(gauge_select, 'gauge')

# visualize on map
gauge_select_mod = gauge_select[['id', 'state', 'county', 'latitude', 'longitude', 'event']].copy()
gauge_select_mod['category'] = 'gauge'
stn_mod = stn[['id', 'state', 'county', 'latitude', 'longitude', 'event']].copy()
stn_mod['category'] = 'stn'
df = pd.concat([gauge_select_mod, stn_mod])
eda_utils.map_event(df)

# create an interactive map
eda_utils.create_interactive_map_event(df)


