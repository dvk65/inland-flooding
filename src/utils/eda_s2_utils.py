"""
This script includes the functions used to analyze the collected Sentinel 2 imagery.

This file can be imported as a module and contains the following functions:
    * organize_satellite - returns a DataFrame containing organized image information with columns 'id', 
                           'images', 'date', 'dir', and 'event'.
    * plot_satellite - plots and save the images for visual inspection
    * filter_satellite - clean the dataset and identify the ideal images
    * TODO
"""

# import libraries
import os
import re
import rasterio
import pandas as pd
from rasterio.plot import show
import matplotlib.pyplot as plt
from utils import global_utils
from datetime import datetime, timedelta


flood_event_periods = global_utils.flood_event_periods

def check_s2_folder(df):
    '''
    Check and delete empty folders (some folders may be empty because there're no image met the requirements)

    Args:
        df: The dataframe representing the collected flood event observations
    '''
    global_utils.print_func_header('delete empty folders')

    event_list = df['event'].unique()
    for event in event_list:
        # construct the paths to the image directories
        event_dir = f'data/img_s2/{event}/'
        event_ndwi_dir = f'data/img_s2/{event}_NDWI/'
        event_cloud_dir = f'data/img_s2/{event}_ClOUD/'

        # check folders and delete if empty
        dirs_to_check = [event_dir, event_ndwi_dir, event_cloud_dir]

        for dir_path in dirs_to_check:
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
                print(f'folders {dirs_to_check} are deleted.')

def create_s2_df(df):
    """
    Create a DataFrame to organize the collected images for flood event observations.
 
    Args:
        df (pd.DataFrame): A DataFrame representing the flood event observations. Each row 
                           in the DataFrame represents an observation of a flood event.
 
    Returns:
        pd.DataFrame: A DataFrame containing organized image information with columns 'filename_vis', 'filename_mask', 'filename_ndwi',
                      'dir', 'date', 'period', 'obs_id', 'event', 'lat', 'lon', 'note', and 'category'.
                      Each row is the DataFrame represents a Sentinel-2 image with its metadata. 
    
    Notes:
        - The DataFrame is also saved as a CSV file at 'data/df_s2/df_s2.csv'.
    """
    print('--------------------------------------------------------------')
    print('Create a DataFrame to organize the collected images...\n')

    # find the event list to iterate over folders storing Sentinel-2 images
    event_list = df['event'].unique()

    # store the image information
    image_data = {}
    for event in event_list:

        # construct the path to the image directory
        event_dir = f'data/img_s2/{event}/'
        if os.path.exists(event_dir):
            if os.listdir(event_dir):

                # iterate over files in the directory
                for filename in os.listdir(event_dir):

                    # extract the image id and date
                    parts = filename.split('_')
                    if parts[0].isdigit():
                        id = parts[0]
                    else:
                        id = '_'.join(parts[:2])
                    check_pattern = r'_(\d{8})T'
                    event_name = event_dir.split('/')[-2]
                    match = re.findall(check_pattern, filename)
                    if match:
                        date = match[0]

                    # retrieve the corresponding NDWI and cloud with shadow mask tif filenames and dirs
                    filename_ndwi = filename.replace('VIS', 'NDWI')
                    filename_cloud = filename.replace('VIS', 'CLOUD')
                    dir_ndwi = f'data/img_s2/{event}_NDWI/'
                    dir_cloud = f'data/img_s2/{event}_ClOUD/'

                    # check if the id is already stored
                    if filename not in image_data:
                        image_data[filename] = {
                            'filename': filename,
                            'filename_ndwi': filename_ndwi,
                            'filename_cloud': filename_cloud,
                            'id': id,
                            'date': date,
                            'dir': event_dir,
                            'dir_ndwi': dir_ndwi,
                            'dir_cloud': dir_cloud,
                            'event': event_name
                        }
                
    # convert the data to a DataFrame
    images_data = list(image_data.values())
    df_s2 = pd.DataFrame(images_data)

    global_utils.describe_df(df_s2, 'image')
    # save to a CSV file
    df_s2.to_csv('data/df_s2/df_s2.csv', index=False)
    return df_s2 

def assign_period_label(row):
    date = datetime.strptime(row['date'], '%Y%m%d')
    
    # category 'gauge'
    if row['category'] == 'gauge':
        event_start = datetime.strptime(row['event_day'], '%Y-%m-%d') - timedelta(days=1)
        event_end = datetime.strptime(row['event_day'], '%Y-%m-%d') + timedelta(days=1)
        if date < event_start:
            return 'before flood'
        elif event_start <= date <= event_end:
            return 'during flood'
        else:
            return 'after flood'
    
    # category 'stn'
    elif row['category'] == 'stn':
        event_start, event_end = row['event_day'].split(' to ')
        start_day = datetime.strptime(event_start, '%Y-%m-%d')
        end_day = datetime.strptime(event_end, '%Y-%m-%d')
        if date < start_day - timedelta(days=1):
            return 'before flood'
        elif start_day - timedelta(days=1) <= date <= end_day + timedelta(days=1):
            return 'during flood'
        else:
            return 'after flood'

def add_metadata_flood_event(flood_event, s2, attr_list):
    global_utils.print_func_header('merge additional information from the flood event dataframe')
    df_s2_mod = s2.copy()
    df_s2_mod = pd.merge(s2, flood_event[attr_list], on='id', how='left')
    df_s2_mod['period'] = df_s2_mod.apply(assign_period_label, axis=1)
    global_utils.describe_df(df_s2_mod, 'image with metadata')

    return df_s2_mod

def check_during_period_label(i):
    return (i['period'] == 'during flood').any()

def filter_df_s2(df):
    '''
    Filter the image dataframe by:
        * dropping duplicate combinations of 'id' and 'date' (overlapping coverage of Sentinel-2 tiles - example: )
        * dropping events without any 'during flood' period label
    '''
    global_utils.print_func_header('filter the image dataframe')
    df_mod = df.copy()
    df_mod = df_mod.drop_duplicates(subset=['id', 'date'])
    df_mod = df_mod.groupby('event').filter(check_during_period_label)
    global_utils.describe_df(df_mod, 'image with metadata (filtered)')

    df_mod.to_csv('data/df_s2/df_s2_mod.csv', index=False)

    print('flood events possibly with Sentinel-2 imagery during flood:\n', df_mod['event'].unique())
    return df_mod

def plot_satellite(df):
    """
    Plot the first 5 images (VIS) for each flood event for visual inspection

    Args:
        df (pd.DataFrame): A DataFrame representing the collected images
    """
    global_utils.print_func_header('plot the first 5 images for each flood event for visual inspection')

    # check the number of rows with the same combination of 'id' and 'period' (indicating that for the same location, there're multiple image during the same period -> identify the best)

    id_period = df.groupby(['id', 'period'])
    duplicate_id_period = id_period.filter(lambda x: len(x) > 1)
    print('number of rows with the same combination of id and period:', len(duplicate_id_period))

    # plot for further inspection
    for event, event_group in df.groupby('event'):
        # select the first five unique ids for the event
        first_five_ids = event_group['id'].unique()[:5]

        for current_id in first_five_ids:
            # filter the data for the current id
            id_group = event_group[event_group['id'] == current_id]
            num_images = len(id_group)
            
            # create a figure for the current id
            fig, axes = plt.subplots(1, num_images, figsize=(15, 5))
            fig.suptitle(f'Event: {event}, ID: {current_id}', fontsize=16)

            if num_images == 1:
                axes = [axes]

            for j, (index, row) in enumerate(id_group.iterrows()):
                image_path = os.path.join(row['dir'], row['filename'])
                if os.path.exists(image_path):
                    with rasterio.open(image_path) as src:
                        show(src, ax=axes[j])
                        axes[j].set_title(f"Date: {row['date']}")
                        axes[j].set_xlim(axes[0].get_xlim())
                        axes[j].set_ylim(axes[0].get_ylim())
                else:
                    axes[j].axis('off')

            plt.tight_layout()
            plt.savefig(f"figs/s2_vis_inspect/{event}_{current_id}_s2.png")
            plt.close(fig)

        print(f"complete - event: {event}")
  
# select the ideal dataset based on plots
def filter_satellite(df):
    '''
    Notes:
        event 2019-11 - date(20191102) during flood identified, date(20191013) less cloud compared to date(20191015) -> drop date(20191015)
        event 2021-09 - not ideal (the change not notable) -> drop event
        event 2023-07 - date(20230711) during flood identified, date(20230726) more frequent compared to date(20230719) -> drop date(20230719)
        event 2023-12 - date(20231220) during flood identified
        event 2024-01 - TODO
        (event 2023-07 is the best event currently - if enough time, consider other events as well)
    '''
    global_utils.print_func_header('select the ideal dataset based on plots')
    df_mod = df.copy()
    df_mod = df[df['event'] == '2023-07']
    df_mod = df_mod[df_mod['date'] != '20230719']

    global_utils.describe_df(df_mod, 'selected image dataset')

    df_mod.to_csv('data/s2_selected.csv', index=False)
    return df_mod