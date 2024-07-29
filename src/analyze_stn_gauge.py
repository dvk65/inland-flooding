"""
This script analyze flood-related dataframes.

This script includes the following steps:
    * step 1 - analyze the collected STN high water mark data.
    * step 2 - analyze the collected high water levels from USGS Water Data Service.
    * step 3 - identify common data ranges between the two datasets and find 
               additional observations from high water levels for the flood events in STN.
"""

# import libraries
import pandas as pd
from utils import analyze_stn_gauge_utils

print('\nStep 1 - ANALYZE STN FLOOD EVENTS (HIGH-WATER MARK)')

# set variables
new_england_list = ["CT", "ME", "MA", "NH", "RI", "VT"]
date_range = {'2021 Henri': ['2021-08-15', '2021-08-23'],
              '2018 March Extratropical Cyclone': ['2018-03-01', '2018-03-05'],
              '2018 January Extratropical Cyclone': ['2018-01-02', '2018-01-06'],
              '2023 July MA NY VT Flood': ['2023-07-10', '2023-07-11'],
              '2023 December East Coast Cyclone': ['2023-12-17', '2023-12-18']}

# load STN high-water mark data
stn = pd.read_csv('data/df_stn/df_stn_mod.csv')

# print an overview of STN high-water mark data
analyze_stn_gauge_utils.desc_data(stn)

# add more precise date ranges for the flood event in STN based on the online report
stn[['formed', 'dissipated']] = stn['event'].apply(lambda x: analyze_stn_gauge_utils.map_dates(x, date_range))
stn = stn.sort_values(by='formed')

# count high water marks by event
analyze_stn_gauge_utils.count_by_group(stn, 'event')

# count high water marks by state
analyze_stn_gauge_utils.count_by_group(stn, 'state')

# visualize high water marks by state
analyze_stn_gauge_utils.plot_bar(stn, 'STN high-water marks', 'stn', new_england_list)

print('\n**********************************************************')
print('Step 2 - ANALYZE GAUGE FLOOD EVENTS (HIGH WATER LEVEL)')

# load gauge high water level data
gauge = pd.read_csv('data/df_gauge/df_gauge_mod.csv')

# print an overview of guage high water level data
gauge = gauge.sort_values(by='event_day')
analyze_stn_gauge_utils.desc_data(gauge)

# count gauge high water level by event
analyze_stn_gauge_utils.count_by_group(gauge, 'event')

# count gauge high water level by state
analyze_stn_gauge_utils.count_by_group(gauge, 'state')

# visualize gauge high water level by state
analyze_stn_gauge_utils.plot_bar(gauge, 'Gauge high water level', 'gauge', new_england_list)

print('\n**********************************************************')
print('Step 3 - ANALYZE STN AND GAUGE')

# explore the flood events documented by both sources
stn_mod = stn.copy()

# convert the event dates in STN dataset (e.g., 2018 March Extratropical Cyclone -> 2018-03)
stn_mod['event'] = stn_mod['event'].replace('2021 Henri', '2021 August Henri')
stn_mod['event'] = analyze_stn_gauge_utils.convert_date(stn_mod)

# compare the flood event dates in both datasets
date_stn_mod_list = stn_mod['event'].unique().tolist()
gauge_select = analyze_stn_gauge_utils.check_overlap(date_stn_mod_list, gauge)

# add the category column in both datasets
stn_mod['category'] = 'stn'
gauge_select['category'] = 'gauge'

# set the start_day and end_day for collecting sentinel 2 imagery
stn_mod['start_day'] = pd.to_datetime(stn_mod['formed']) - pd.Timedelta(days=20)
stn_mod['end_day'] = pd.to_datetime(stn_mod['dissipated']) + pd.Timedelta(days=20)

gauge_select['start_day'] = pd.to_datetime(gauge_select['event_day']) - pd.Timedelta(days=20)
gauge_select['end_day'] = pd.to_datetime(gauge_select['event_day']) + pd.Timedelta(days=20)

# combine two datasets
attr_list = ['id', 'event', 'state', 'county', 'latitude', 'longitude', 'note', 'category', 'start_day', 'end_day']
df = pd.concat([stn_mod[attr_list], gauge_select[attr_list]])

# print an overview of the combined dataset
analyze_stn_gauge_utils.desc_data(df)

# save the modified datasets 
stn_mod.to_csv('data/flood_events_stn.csv', index=False)
gauge_select.to_csv('data/flood_events_gauge.csv', index=False)
df.to_csv('data/flood_events.csv', index=False)

# visualize the flood events in the gauge dataset that are also documented in the stn dataset
analyze_stn_gauge_utils.plot_bar(gauge_select, 'Gauge high water levels (also shown in STN)', 'stn_in_gauge', new_england_list)

# visualize the flood events (combination of stn and gauge_select)
analyze_stn_gauge_utils.plot_bar(df, 'Combination (STN and Gauge selected)', 'stn_and_gauge', new_england_list)

# visualize all flood events on map
analyze_stn_gauge_utils.map_event(df)
analyze_stn_gauge_utils.map_event_interactive(df)


