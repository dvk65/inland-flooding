# import libraries
import pandas as pd
from utils import eda_utils

# create a dataframe to check the stored images
stn = pd.read_csv('data/stn/stn_flood_event_mod.csv')
event_list = stn['event'].unique()
event_list = ['2021 Henri']
event_list_mod = [event.replace(' ', '_') for event in event_list]
# event_images_df = eda_utils.check_satellite(event_list_mod)

# preprocess the dataframe
# eda_utils.prep_satellite(event_images_df)

# select images