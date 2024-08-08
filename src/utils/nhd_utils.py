"""
This script includes the functions related to National Hydrography Dataset. 

This script can be imported as a module and includes the following functions:
    * download_nhd_shape - downloads the National Hydrography Dataset Flowline for specified states;
    * add_nhd_layer_s2 - plots the NHD flowlines on top of Sentinel-2 images during flood events for visual inspection.
"""

# import libraries
import os
import requests
import zipfile
import geopandas as gpd
from rasterio.plot import show
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from utils import global_utils, kmeans_utils
from matplotlib.colors import ListedColormap
from pyproj import Transformer



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

def read_ndwi_tif(file_path, threshold=-0.1):

    with rasterio.open(file_path) as src:
        ndwi_mask = src.read(1) 

    binary_water_mask = ndwi_mask > threshold

    return binary_water_mask

def apply_cloud_mask(image, cloud_mask_path):

    with rasterio.open(cloud_mask_path) as src:
        cloud_mask = src.read(1)

    valid_mask = cloud_mask == 0
    result = np.where(valid_mask, image, np.nan)

    return result

def add_nhd_layer_s2(df, area, area_abbr_list):
    '''
    Plot the NHD flowlines on top of Sentinel-2 images during flood events for visual inspection

    Args:
        df (pd.DataFrame): The selected DataFrame used to add NHD flowline layer
        area (list of str): The specified area (state)
        area_abbr_list (dict): A dictionary mapping full state names to their abbreviations
    '''
    global_utils.print_func_header('add NHD flowline above Sentinel-2 and plot the result')
    for i in area:

        # read the shapefile into a GeoDataFrame
        shp_path = f'data/nhd/{i}/Shape/NHDFlowline.shp'

        # flowline['fcode'] (might be helpful for extracting major river?) -> [55800 46003 46006 33600 56600 33400 42801 42816 42803 33601 46000 42807 33603 42820 42813 42800]
        flowline = gpd.read_file(shp_path)

        # filter the DataFrame for the current state's data during the flood event
        i_abbr = area_abbr_list[i]
        df_i = df[df['state'] == i_abbr]
        unique_ids = df_i['id'].unique()
        global_utils.plot_helper(unique_ids, df_i, 's2_nhd', 's2_nhd', flowline)

        # plot all the mask (original Sentinel-2, NDWI mask, flowline) for each image
        for _, row in df_i.iterrows():
            image_path = os.path.join(row['dir'], row['filename'])
            ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
            cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
            _, sat_bounds, tiff_crs, _, _  = kmeans_utils.read_tif(image_path) 

            ndwi_mask = read_ndwi_tif(ndwi_path)
            ndwi_mask = apply_cloud_mask(ndwi_mask, cloud_path)

            # extract the flowline mask
            if flowline.crs != tiff_crs:
                flowline = flowline.to_crs(tiff_crs)

            fig, axes = plt.subplots(1, 4, figsize=(40, 10))

            # plot satellite image
            lat = row['latitude']
            lon = row['longitude']
            with rasterio.open(image_path) as src:
                show(src, ax=axes[0], title='Satellite image')
                transformer = Transformer.from_crs("EPSG:4326", tiff_crs, always_xy=True)
                raster_x, raster_y = transformer.transform(lon, lat)
                axes[0].plot(raster_x, raster_y, 'ro', markersize=6, zorder=3)

            # plot satellite image with flowline
            with rasterio.open(image_path) as src:
                show(src, ax=axes[1], title='Satellite Image with Flowline')
            flowline.plot(ax=axes[1], color='cyan', linewidth=0.5)
            axes[1].set_xlim(sat_bounds.left, sat_bounds.right)
            axes[1].set_ylim(sat_bounds.bottom, sat_bounds.top)

            # plot NDWI mask
            cmap = plt.cm.gray
            cmap.set_bad(color='black')
            axes[2].imshow(ndwi_mask, cmap=cmap)
            axes[2].set_title('NDWI mask')
            axes[2].axis('off')

            # plot cloud mask
            with rasterio.open(cloud_path) as src:
                cloud_mask = src.read(1) 
            axes[3].imshow(cloud_mask, cmap='gray')
            axes[3].set_title('Cloud Mask')
            axes[3].axis('off')

            plt.tight_layout()
            output_filename = f"{row['filename'].replace('.tif', '')}_all_masks.png"
            plt.savefig(f'figs/s2_all_masks/{output_filename}')
            plt.close(fig)

