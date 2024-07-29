"""
This script includes the functions used to analyze the collected Sentinel 2 imagery.

This file can be imported as a module and contains the following functions:
    * organize_satellite - returns a DataFrame containing organized image information with columns 'id', 
                           'images', 'date', 'dir', and 'event'.
    * plot_satellite - plots and save the images for visual inspection
    * filter_satellite - clean the dataset and identify the ideal images
    * read_tif - 
    * calculate_difference - 
    * create_combined_cloud_mask -
    * calculate_change - 
"""

# import libraries
import os
import re
import rasterio
import numpy as np
import pandas as pd
from rasterio.plot import show
import matplotlib.pyplot as plt

def organize_satellite(df):
    """
    Create a DataFrame to organize the collected images for flood event observations.
 
    Args:
        df (pd.DataFrame): A DataFrame representing the flood event observations. Each row 
                           in the DataFrame represents an observation of a flood event.
 
    Returns:
        pd.DataFrame: A DataFrame containing organized image information with columns 'id', 
                      'images', 'date', 'dir', and 'event'.
    
    Notes:
        - The DataFrame is also saved as a CSV file at 'data/sentinel2_df/images_df.csv'.
        - For each observation, images for the same day are not added again. (overlapping coverage of Sentinel-2 tiles)
    """
    print('--------------------------------------------------------------')
    print('Create a DataFrame to organize the collected images...\n')
    # store the image information organized by the ids
    id_images = {}
    for event in df:

        # construct the path to the image directory
        event_dir = f'data/img_sentinel2/{event}/'
        if os.path.exists(event_dir):

            # iterate over files in the directory
            for filename in os.listdir(event_dir):

                # extract the image id and date
                parts = filename.split('_')
                id = parts[0]
                check_pattern = r'_(\d{8})T'
                event_name = event_dir.split('/')[-2]
                match = re.findall(check_pattern, filename)
                if match:
                    date = match[0]

                # check if the id is already stored
                if id not in id_images:
                    id_images[id] = {
                        'id': id,
                        'images': [],
                        'date': [],
                        'dir': event_dir,
                        'event': event_name
                    }

                # check if the date is already stored for this id
                if date not in id_images[id]['date']:
                    id_images[id]['images'].append(filename)
                    id_images[id]['date'].append(date)
                
    # convert the data to a DataFrame
    images_data = list(id_images.values())
    images_df = pd.DataFrame(images_data)

    print('observations (flood event ids with images):\n', images_df['id'].values)

    # save to a CSV file
    images_df.to_csv('data/df_sentinel2/images_df.csv', index=False)
    return images_df 

def plot_satellite(df):
    """
    Plot the satellite images for each flood event observation
 
    Args:
        df (pd.DataFrame): A DataFrame representing the flood event observations. Each row 
                           in the DataFrame represents an observation of a flood event.
 
    Returns:
        pd.DataFrame: A DataFrame containing organized image information with columns 'id', 
                      'images', 'date', 'dir', and 'event'.
    
    Notes:
        - The DataFrame is also saved as a CSV file at 'data/sentinel2_df/images_df.csv'.
        - For each observation, images for the same day are not added again. (overlapping coverage of Sentinel-2 tiles)
    """
    print('--------------------------------------------------------------')
    print('Plot the collected images...\n')
    event_list = df['dir'].unique()
    for event in event_list:
        event_df = df[df['dir'] == event].reset_index(drop=True)
        for index, row in event_df[:5].iterrows():
            event_name = row['event']
            num_images = len(row['images'])
            fig, axes = plt.subplots(1, num_images, figsize=(5 * num_images, 5))
            fig.suptitle(f"Event: {event_name}; ID: {row['id']}", fontsize=16)
            if num_images == 1:
                axes = [axes]
            for i in range(num_images):
                check_pattern = r'_(\d{8})T'
                match = re.findall(check_pattern, row['images'][i])
                if match:
                    date = match[0]
                image_path = os.path.join(row['dir'], row['images'][i])
                if os.path.exists(image_path):
                    with rasterio.open(image_path) as src:
                        show(src, ax=axes[i])
                        axes[i].set_title(f"Date: {date}")
                        axes[i].set_xlim(axes[0].get_xlim())
                        axes[i].set_ylim(axes[0].get_ylim())
                else:
                    axes[i].axis('off')
            plt.tight_layout()
            plt.savefig(f"figs/image_group_by_id/{event_name}_{row['id']}_sentinel2.png")
            plt.close(fig)
        print(f"complete - event: {event}")
  
# select the ideal flood event ids
def filter_satellite(df):

    df_mod = df.copy()
    df_mod['before'] = df_mod.apply(lambda row: row['images'][row['date'].index('20230706')] if '20230706' in row['date'] else None, axis=1)
    df_mod['during'] = df_mod.apply(lambda row: row['images'][row['date'].index('20230711')] if '20230711' in row['date'] else None, axis=1)
    df_mod['after'] = df_mod.apply(lambda row: row['images'][row['date'].index('20230726')] if '20230726' in row['date'] else None, axis=1)

    df_mod = df_mod.dropna(subset=['during'])    
    return df_mod

# plot the filitered flood events
def plot_filter_satellite(df):
    print('--------------------------------------------------------------')
    print('Plot the filtered images (before/during/after)...\n')
    for index, row in df.iterrows():
        before_image_path = os.path.join(row['dir'], row['before'])
        during_image_path = os.path.join(row['dir'], row['during'])
        after_image_path = os.path.join(row['dir'], row['after'])
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f"ID: {row['id']}", fontsize=16)

        with rasterio.open(before_image_path) as src:
            show(src, ax=axes[0])
            axes[0].set_title('Before')

        with rasterio.open(during_image_path) as src:
            show(src, ax=axes[1])
            axes[1].set_title('During')

        with rasterio.open(after_image_path) as src:
            show(src, ax=axes[2])
            axes[2].set_title('After')

        plt.tight_layout()
        plt.savefig(f"figs/image_selected/{row['id']}_sentinel2_filter.png")
        plt.close(fig)  

def read_tif(file_path):
    with rasterio.open(file_path) as src:
        return src.read(), src.profile
  
def calculate_difference(image1, image2):
    return np.abs(image1 - image2)

def create_combined_cloud_mask(cloud_mask1, cloud_mask2):
    with rasterio.open(cloud_mask1) as cloud_src1:
        mask1 = cloud_src1.read(1)
    with rasterio.open(cloud_mask2) as cloud_src2:
        mask2 = cloud_src2.read(1)
    combined_cloud_mask = np.logical_or(mask1 == 1, mask2 == 1).astype(np.uint8)
    return combined_cloud_mask

def calculate_change(df):

    for index, row in df.iterrows():
        dir_mod = row['dir'].rstrip('/')
        before_image_path = os.path.join(dir_mod, row['before'])
        cloud_before_file_name = row['before'].replace("_VIS.tif", "_CLOUD.tif")
        cloud_before_file_path = f"{dir_mod}_CLOUD/{cloud_before_file_name}"

        during_image_path = os.path.join(dir_mod, row['during'])
        cloud_during_file_name = row['during'].replace("_VIS.tif", "_CLOUD.tif")
        cloud_during_file_path = f"{dir_mod}_CLOUD/{cloud_during_file_name}"

        after_image_path = os.path.join(dir_mod, row['after'])
        cloud_after_file_name = row['after'].replace("_VIS.tif", "_CLOUD.tif")
        cloud_after_file_path = f"{dir_mod}_CLOUD/{cloud_after_file_name}"

        image1, profile1 = read_tif(before_image_path)
        image2, profile1 = read_tif(during_image_path)
        image3, profile1 = read_tif(after_image_path)

        cloud_mask1, _ = read_tif(cloud_before_file_path)
        cloud_mask2, _ = read_tif(cloud_during_file_path)
        cloud_mask3, _ = read_tif(cloud_after_file_path)

        cloud_mask1_bool = cloud_mask1.astype(bool)
        cloud_mask2_bool = cloud_mask2.astype(bool)
        cloud_mask3_bool = cloud_mask3.astype(bool)
        image1_masked = np.where(cloud_mask1_bool, np.nan, image1)
        image2_masked = np.where(cloud_mask2_bool, np.nan, image2)
        image3_masked = np.where(cloud_mask3_bool, np.nan, image3)

        difference_image_12 = np.abs(image1_masked - image2_masked)
        difference_image_23 = np.abs(image2_masked - image3_masked)

        difference_image_12[np.isnan(difference_image_12)] = 0
        difference_image_23[np.isnan(difference_image_23)] = 0

        difference_image_normalized_12 = (difference_image_12 - np.nanmin(difference_image_12)) / (np.nanmax(difference_image_12) - np.nanmin(difference_image_12))
        difference_image_normalized_23 = (difference_image_23 - np.nanmin(difference_image_23)) / (np.nanmax(difference_image_23) - np.nanmin(difference_image_23))

        fig = plt.figure(figsize=(18, 6))
        fig.suptitle(f"ID: {row['id']}", fontsize=16)

        plt.subplot(1, 5, 1)
        plt.title('Before')
        plt.imshow(image1.transpose(1, 2, 0))

        plt.subplot(1, 5, 2)
        plt.title('Before vs During')
        plt.imshow(difference_image_normalized_12[0])

        plt.subplot(1, 5, 3)
        plt.title('During')
        plt.imshow(image2.transpose(1, 2, 0))

        plt.subplot(1, 5, 4)
        plt.title('During vs After')
        plt.imshow(difference_image_normalized_23[0])

        plt.subplot(1, 5, 5)
        plt.title('After')
        plt.imshow(image3.transpose(1, 2, 0))

        plt.tight_layout()
        plt.savefig(f"figs/image_before_during_after_abs_diff/{row['id']}_sentinel2_abs_diff.png")
        plt.close(fig)

