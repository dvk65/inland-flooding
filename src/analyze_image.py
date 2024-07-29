"""
This script runs the analysis for the collected Sentinel 2 images and identifies the ideal dataset for the KMeans clustering algorithm. 

This file contains the following steps:
    * step 1 - create a dataframe to store and organize the image information.
    * step 2 - plot the collect images for visual inspection.
    * step 3 - clean the dataset to extract the ideal image datasets for KMeans clustering
    * step 4 - plot all filtered images organized by ids
    * step 5 - drop the unwanted instances
"""

# import libraries
import pandas as pd
from utils import analyze_image_utils

# load the dataset
df = pd.read_csv('data/flood_events.csv')

# step 1 - create a dataframe to check the stored images
event_list = df['event'].unique()
event_images_df = analyze_image_utils.organize_satellite(event_list)

# plot the images to identify the ideal events and dates
analyze_image_utils.plot_satellite(event_images_df)

# # select images for the kmeans clustering
event_202307 = event_images_df[event_images_df['event'] == '2023-07']
event_202307_mod = analyze_image_utils.filter_satellite(event_202307)

# # plot the filtered dataframe
analyze_image_utils.plot_filter_satellite(event_202307_mod)

# # drop the low-quality image (cloud cover during the flood event)
drop_list = ['44972']
image_kmeans = event_202307_mod[~event_202307_mod['id'].isin(drop_list)]
image_kmeans.to_csv('data/image_kmeans.csv', index=False)

# # check the difference
analyze_image_utils.calculate_change(image_kmeans)