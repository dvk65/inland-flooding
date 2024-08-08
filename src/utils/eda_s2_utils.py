"""
This script includes the functions used to organize and analyze the collected Sentinel 2 image dataset.

This file can be imported as a module and contains the following functions:
    * check_s2_folder - delete empty folders;
    * create_s2_df - returns a DataFrame containing organized image information;
    * assign_period_label - returns a label indicating whether it was taken before, during, or after a flood event;
    * add_metadata_flood_event - returns a DataFrame with additional flood-related information;
    * check_during_period_label - returns True if any observation within the specified group is labeled as 'during flood';
    * filter_df_s2 - return the filtered dataset;
    * plot_helper - plot images by ids;
    * plot_s2 - plots the image grouped by ids for visual inspection;
    * check_cloud_cover - returns the percentage of cloud and shadow coverage;
    * select_s2 - decide the ideal dataset;
"""

# import libraries
import os
import re
import rasterio
import pandas as pd
import numpy as np
from rasterio.plot import show
import matplotlib.pyplot as plt
from utils import global_utils
from datetime import datetime, timedelta
from pyproj import Transformer



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
        event_cloud_dir = f'data/img_s2/{event}_CLOUD/'

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
                    dir_cloud = f'data/img_s2/{event}_CLOUD/'

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

def assign_period_label(row, day_adjust_dict):
    """
    Assign labels to the image indicating whether it was taken before, during, or after a flood event

    Args:
        row (pd.Series): A row of data containing information about the image and the event

    Returns:
        str: A label indicating whether it was taken before, during, or after a flood event
    """
    date = datetime.strptime(row['date'], '%Y%m%d')
    source = row['source']
    start_adjust, end_adjust = day_adjust_dict.get(source, (0, 0))

    # category 'gauge'
    if source == 'gauge':
        # adjust using +/- timedelta(days=i) after analyzing s2_selected ()
        event_start = datetime.strptime(row['event_day'], '%Y-%m-%d') - timedelta(days=start_adjust)
        event_end = datetime.strptime(row['event_day'], '%Y-%m-%d') + timedelta(days=end_adjust)
        if date < event_start:
            return 'before flood'
        elif event_start <= date <= event_end:
            return 'during flood'
        else:
            return 'after flood'
    
    # category 'stn'
    elif source == 'stn':
        # adjust using +/- timedelta(days=i) after analyzing s2_selected ()
        event_start, event_end = row['event_day'].split(' to ')
        start_day = datetime.strptime(event_start, '%Y-%m-%d') - timedelta(days=start_adjust)
        end_day = datetime.strptime(event_end, '%Y-%m-%d') + timedelta(days=end_adjust)
        if date < start_day:
            return 'before flood'
        elif start_day <= date <= end_day:
            return 'during flood'
        else:
            return 'after flood'

def add_metadata_flood_event(flood_event, s2, attr_list, day_adjust_dict):
    """
    Add additional information to the image dataframe

    Args:
        flood_event (pd.DataFrame): The DataFrame with high-water marks and high-water levels
        s2 (pd.DataFrame): The DataFrame with image information
        attr_list (list of str): The specified attributes to be selected

    Returns:
        pd.DataFrame: The DataFrame with additional information added
    """
    global_utils.print_func_header('merge additional information from the flood event dataframe')
    df_s2_mod = s2.copy()
    df_s2_mod = pd.merge(s2, flood_event[attr_list], on='id', how='left')
    df_s2_mod['period'] = df_s2_mod.apply(assign_period_label, axis=1, day_adjust_dict=day_adjust_dict)
    global_utils.describe_df(df_s2_mod, 'image with metadata')

    return df_s2_mod

def check_during_period_label(i):
    """
    Check if any image is labeled as 'during flood'

    Args:
        i (pd.Series): A Series representing a group of observations to be checked

    Returns:
        bool: True if any observation within the group has a period label of during flood; otherwise, False    
    """
    return (i['period'] == 'during flood').any()

def filter_df_s2(df):
    '''
    Filter the image dataframe by:
        * dropping duplicate combinations of 'id' and 'date' (overlapping coverage of Sentinel-2 tiles - example: )
        * dropping events without any 'during flood' period label

    Args:
        df (pd.DataFrame): The specified DataFrame to be filtered

    Returns:
        pd.DataFrame: The filtered dataset
    '''
    global_utils.print_func_header('filter the image dataframe')
    df_mod = df.copy()
    df_mod = df_mod.drop_duplicates(subset=['id', 'date'])
    df_mod = df_mod.groupby('event').filter(check_during_period_label)
    global_utils.describe_df(df_mod, 'image with metadata (filtered)')

    df_mod.to_csv('data/df_s2/df_s2_mod.csv', index=False)

    print('flood events possibly with Sentinel-2 imagery during flood:\n', df_mod['event'].unique())
    return df_mod

def plot_s2(df):
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

        global_utils.plot_helper(first_five_ids, event_group, 's2_vis_inspect', 's2')

        print(f"complete - event: {event}")

def check_cloud_cover(path):
    """
    Calculate the percentage of cloud and shadow cover in the image

    Args:
        path (str): The path of cloud maks
    
    Returns:
        float: The percentage of cloud and shadow mask
    """
    with rasterio.open(path) as src:
        cloud_mask = src.read(1)
        cloud_percentage = np.mean(cloud_mask == 1) * 100
        return cloud_percentage

def select_s2(df, event_selection, cloud_threshold, date_drop, flood_day_adjust_dict=None, explore=None):
    '''
    Select the ideal image datasets based on plots

    Args:
        df (pd.DataFrame): The specified DataFrame to be selected

    Returns:
        pd.DataFrame: The ready-to-use dataset for KMeans clustering

    Notes:
        event 2019-11 - date(20191102) during flood identified (land color close to the flooding river)
        event 2021-09 - not ideal (the change not notable)
        event 2023-07 - date(20230711) during flood identified
        event 2023-12 - date(20231220) during flood identified (snow cover on the image before flood and land color close to the flooding river)
        event 2024-01 - not ideal (the change not notable)
        (event 2023-07 is the best event currently - if enough time, consider other events as well)
    '''
    global_utils.print_func_header('select the ideal event based on plots')
    df_mod = df[df['event'].isin(event_selection)].copy()
    df_mod = df_mod.reset_index(drop=True)
    unique_ids = df_mod['id'].unique()
    global_utils.describe_df(df_mod, 'selected image dataset')

    print(f'\nplot the selected images for further inspection')
    global_utils.plot_helper(unique_ids, df_mod, 's2_selected', 's2_selected')

    if explore == 'complete':
        df_mod['period'] = df_mod.apply(assign_period_label, axis=1, day_adjust_dict=flood_day_adjust_dict)
        df_ready = df_mod[~df_mod['date'].isin(date_drop)].copy()
        drop_list = []
        for index, row in df_ready.iterrows():
            cloud_mask_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
            cloud_percentage = check_cloud_cover(cloud_mask_path)
            if cloud_percentage > cloud_threshold:
                drop_list.append(index)
        
        df_ready.drop(drop_list, inplace=True)
        df_ready.reset_index(drop=True, inplace=True)
        unique_ids = df_ready['id'].unique()
        global_utils.describe_df(df_ready, 'ready-to-use image dataset')

        # check the images during flood
        df_during_flood = df_ready[df_ready['period'] == 'during flood']
        print("\nnumber of images collected during flood:\n", df_during_flood.shape[0])
        print("\nimages collected during flood:\n", df_during_flood['id'].tolist())

        print(f'\nplot the ready-to-use images for verification')
        global_utils.plot_helper(unique_ids, df_ready, 's2_ready', 's2_ready')

        df_ready.to_csv('data/s2.csv', index=False)

    return df_mod

def test_ndwi_tif(file_path, threshold_list):
    global_utils.print('explore and define ndwi mask threshold')
    base_name = os.path.basename(file_path)
    filename = base_name.replace('_NDWI.tif', '')
    with rasterio.open(file_path) as src:
        ndwi_mask = src.read(1)

    fig, axes = plt.subplots(1, len(threshold_list), figsize=(20, 5))
    for ax, threshold in zip(axes, threshold_list):
        binary_water_mask = ndwi_mask > threshold 
        ax.imshow(binary_water_mask, cmap='gray')
        ax.set_title(f'Threshold: {threshold}')
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(f'figs/s2_ndwi/{filename}_NDWI_test.png')
    plt.close()