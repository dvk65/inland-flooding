"""
This script includes the functions used to organize and analyze the collected Sentinel 2 image dataset.

This file can be imported as a module and contains the following functions:
    * check_s2_folder - delete empty folders;
    * create_s2_df - return a DataFrame containing organized image information;
    * assign_period_label - return a label indicating whether it was taken before, during, or after a flood event;
    * add_metadata_flood_event - return a DataFrame with additional flood-related information;
    * plot_s2 - plot the image grouped by ids for visual inspection;
    * check_cloud_cover - return the percentage of cloud and shadow coverage;
    * select_s2 - return the ideal dataset;
    * test_ndwi_tif - plot the results of applying different NDWI threshold values to identify water areas;
    * download_nhd_shape - download the flowline shapefiles for specified states;
    * add_nhd_layer_s2 - plot flowlines on top of Sentinel-2 images and plot other figures (Sentinel-2, cloud mask, NDWI mask) individually
"""

# import libraries
import os
import re
import requests
import zipfile
import rasterio
import pandas as pd
import numpy as np
import geopandas as gpd
from pyproj import Transformer
from rasterio.plot import show
import matplotlib.pyplot as plt
from utils import global_utils, kmeans_utils
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
        day_adjust_dict (dict):  A dictionary to assign period (before, during, or after flood)
        
    Returns:
        str: A label indicating whether it was taken before, during, or after a flood event
    """
    date = datetime.strptime(row['date'], '%Y%m%d')
    source = row['source']
    start_adjust, end_adjust = day_adjust_dict[source]

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
        day_adjust_dict (dict): A dictionary to assign period (before, during, or after flood)

    Returns:
        pd.DataFrame: The DataFrame with additional information added
    """
    global_utils.print_func_header('merge additional information from the flood event dataframe')
    df_s2_mod = s2.copy()
    df_s2_mod = pd.merge(s2, flood_event[attr_list], on='id', how='left')
    df_s2_mod['period'] = df_s2_mod.apply(assign_period_label, axis=1, day_adjust_dict=day_adjust_dict)
    global_utils.describe_df(df_s2_mod, 'image with metadata')

    df_s2_mod.to_csv('data/df_s2/df_s2_mod.csv', index=False)
    return df_s2_mod

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

        global_utils.plot_helper(first_five_ids, event_group, 's2_raw_vis_by_id')

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
        event_selection (list of str): A list of events used to filter the DataFrame
        cloud_threshold (int): A threshold to drop image with much cloud
        date_drop (list of str): A list of image date used to filter teh DataFrame
        flood_day_adjust_dict (dict): A dictionary used to adjust period labels in `assign_period_label`
        explore (str): If set to 'complete', additional cleaning steps are added. If None, only process event_selection and plot for examination

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
    df_mod = df_mod.drop_duplicates(subset=['id', 'date'])
    df_mod = df_mod.reset_index(drop=True)
    unique_ids = df_mod['id'].unique()
    global_utils.describe_df(df_mod, 'selected image dataset')

    print(f'\nplot the selected images for further inspection')
    global_utils.plot_helper(unique_ids, df_mod, 's2_event_selected')

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
        global_utils.plot_helper(unique_ids, df_ready, 's2_cleaned')

        df_ready.to_csv('data/s2.csv', index=False)
        return df_ready
    else:
        return df_mod

def test_ndwi_tif(df, threshold_list):
    """
    Test different NDWI threshold values to identify water areas

    Args:
        df (pd.DataFrame): A DataFrame used to test NDWI threshold
        threshold_list (list of str): A list of NDWI threshold values
    """
    global_utils.print_func_header(f'test ndwi threshold list {threshold_list}')
    for _, row in df.iterrows():
        file_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
        cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
        base_name = os.path.basename(file_path)
        global_utils.print_func_header(f'explore and define ndwi mask threshold for {base_name}')
        filename = base_name.replace('_NDWI.tif', '')
        with rasterio.open(file_path) as src:
            ndwi_mask = src.read(1)

        ndwi_mask = global_utils.apply_cloud_mask(ndwi_mask, cloud_path)

        fig, axes = plt.subplots(1, len(threshold_list), figsize=(4 * len(threshold_list), 5))
        fig.suptitle(f'NDWI threshold exploration for {filename}')
        for ax, threshold in zip(axes, threshold_list):
            binary_water_mask = ndwi_mask > threshold 
            ax.imshow(binary_water_mask, cmap='gray')
            ax.set_title(f'threshold: {threshold}')
            ax.axis('off')

        plt.tight_layout()
        plt.savefig(f"figs/s2_ndwi_test/{row['id']}_{row['date']}_NDWI_test.png")
        plt.close()
        print(f"complete - {filename}")

def download_nhd_shape(area_list, content_list):
    """
    Download the National Hydrography Dataset Flowline for specified states

    Args:
        area_list (list of str): The specified states for which NHD data needs to be collected
        content_list: The specified components of the NHD data
    """
    global_utils.print_func_header('download NHD')
    for i in area_list:

        # construct URL to download NHD (e.g., https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_Vermont_State_Shape.zip)
        url = f'https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_{i}_State_Shape.zip'

        # download the ZIP file to the specified directory
        dir = f'data/nhd/{i}'
        os.makedirs(dir, exist_ok=True)
        name = os.path.basename(url)
        file_path = os.path.join(dir, name)
        res = requests.get(url)
        with open(file_path, 'wb') as f:
            f.write(res.content)
        print(f'download NHD for {i} - {name}')

        # extract the flowline-related files 
        with zipfile.ZipFile(file_path, 'r') as z:
            contents = z.namelist()
            
            for item in content_list:
                if item in contents:
                    z.extract(item, dir)
                    print(f'\nextract {i} {item}')

        # delete the ZIP file
        os.remove(file_path)

    # explore the contents within the ZIP file
    print(f'list all contents within the ZIP file for {i}')
    print(contents)

def add_nhd_layer_s2(df, area, area_abbr_list):
    '''
    Plot the NHD flowlines on top of Sentinel-2 images and plot other figures (Sentinel-2, cloud mask, NDWI mask) individually

    Args:
        df (pd.DataFrame): The selected DataFrame used to add NHD flowline layer
        area (list of str): The specified area (state)
        area_abbr_list (dict): A dictionary mapping full state names to their abbreviations
    '''
    global_utils.print_func_header('plot image and all masks (cloud, NDWI, flowline) individually')
    for i in area:

        # read the shapefile into a GeoDataFrame
        shp_path = f'data/nhd/{i}/Shape/NHDFlowline.shp'

        # flowline['ftype'] or ['fcode'] (might be helpful for extracting major river?) 
        major_river = [558]
        flowline = gpd.read_file(shp_path)
        major_rivers = flowline[(flowline['ftype'].isin(major_river)) & (flowline['lengthkm'] >= 0.6)]

        # filter the DataFrame for the current state's data during the flood event
        i_abbr = area_abbr_list[i]
        df_i = df[df['state'] == i_abbr]

        # plot all the mask (original Sentinel-2, NDWI mask, flowline) for each image
        for _, row in df_i.iterrows():
            image_path = os.path.join(row['dir'], row['filename'])
            ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
            cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
            _, sat_bounds, tiff_crs, _, _  = kmeans_utils.read_tif(image_path) 

            ndwi_mask = global_utils.read_ndwi_tif(ndwi_path)
            ndwi_mask = global_utils.apply_cloud_mask(ndwi_mask, cloud_path)

            # extract the flowline mask
            if major_rivers.crs != tiff_crs:
                major_rivers = major_rivers.to_crs(tiff_crs)

            # plot satellite image
            lat = row['latitude']
            lon = row['longitude']
            transformer = Transformer.from_crs("EPSG:4326", tiff_crs, always_xy=True)
            raster_x, raster_y = transformer.transform(lon, lat)

            fig, ax = plt.subplots(figsize=(10, 10))
            with rasterio.open(image_path) as src:
                show(src, ax=ax, title=f"S2 - ID: {row['id']}, Date: {row['date']}")
                ax.plot(raster_x, raster_y, 'ro', markersize=6, zorder=3)
            plt.tight_layout()
            output_filename = f"{row['id']}_{row['date']}_s2.png"
            plt.savefig(f'figs/s2/{output_filename}')
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(10, 10))
            with rasterio.open(image_path) as src:
                show(src, ax=ax, title=f"S2 with flowline - ID: {row['id']}, Date: {row['date']}")
            major_rivers.plot(ax=ax, color='cyan', linewidth=0.5)
            ax.set_xlim(sat_bounds.left, sat_bounds.right)
            ax.set_ylim(sat_bounds.bottom, sat_bounds.top)
            plt.tight_layout()
            output_filename = f"{row['id']}_{row['date']}_s2_flowline.png"
            plt.savefig(f'figs/s2/{output_filename}')
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(10, 10))
            cmap = plt.cm.gray
            cmap.set_bad(color='black')
            ax.imshow(ndwi_mask, cmap=cmap)
            ax.set_title(f"NDWI - ID: {row['id']}, Date: {row['date']}")
            ax.axis('off')
            plt.tight_layout()
            output_filename = f"{row['id']}_{row['date']}_ndwi.png"
            plt.savefig(f'figs/s2/{output_filename}')
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(10, 10))
            with rasterio.open(cloud_path) as src:
                cloud_mask = src.read(1) 
            ax.imshow(cloud_mask, cmap='gray')
            ax.set_title(f"Cloud - ID: {row['id']}, Date: {row['date']}")
            ax.axis('off')
            plt.tight_layout()
            output_filename = f"{row['id']}_{row['date']}_cloud.png"
            plt.savefig(f'figs/s2/{output_filename}')
            plt.close(fig)

            print(f"complete - plot image and all masks individually {row['filename']}")
        
        print(f"complete - {i}")