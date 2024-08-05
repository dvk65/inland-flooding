"""
This script is used to collect and explore the National Hydrography Dataset for specified states.

The National Hydrography Dataset will be used to analyze the Sentinel-2 images and identify potential flooding areas
"""
# import libraries
import time
import pandas as pd
from utils import global_utils, nhd_utils

# track the runtime
start = time.time()
print('\nSTART - NHD DATA COLLECTION AND PLOTTING\n')

# identify the states for which NHD data needs to be collected
area_abbr_list = global_utils.area_abbr_list
df = pd.read_csv('data/s2.csv')
area_in_df = df['state'].unique().tolist()
area_list = [state for state, abbr in area_abbr_list.items() if abbr in area_in_df]

# specify the required components (flowline) of the NHD data
# question - There's one file called Shape/NHDFlowlineVAA.dbf. Meaning?
content_selected = ['Shape/NHDFlowline.shp', 'Shape/NHDFlowline.shx', 'Shape/NHDFlowline.dbf', 'Shape/NHDFlowline.prj']

# download and extract the NHD shapefiles for specified states
nhd_utils.download_nhd_shape(area_list, content_selected)

# plot the NHD flowlines on top of Sentinel-2 images for visual inspection
nhd_utils.add_nhd_layer_s2(df, area_list, area_abbr_list)
print('\nCOMPLETE - NHD DATA COLLECTION AND PLOTTING\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')