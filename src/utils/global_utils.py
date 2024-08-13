"""
This script includes the functions used as a module in multiple scripts.  

This file can be imported as a module and includes the following functions:
    * print_func_header - print a summary of the running function;
    * collect_nhd - returns a list of GeoDataFrames, each representing an NHD layer.
"""
# import libaries
import os
import matplotlib.pyplot as plt

import rasterio
import numpy as np
import geopandas as gpd
from rasterio.plot import show
from pyproj import Transformer


flood_event_periods = {'2021 Henri': ['2021-08-15', '2021-08-23'],
              '2018 March Extratropical Cyclone': ['2018-03-01', '2018-03-05'],
              '2018 January Extratropical Cyclone': ['2018-01-02', '2018-01-06'],
              '2023 July MA NY VT Flood': ['2023-07-10', '2023-07-11'],
              '2023 December East Coast Cyclone': ['2023-12-17', '2023-12-18']}

area_abbr_list = {'Connecticut': 'CT', 'Maine': 'ME', 
                  'Massachusetts': 'MA', 'New Hampshire': 'NH', 
                  'Rhode Island': 'RI', 'Vermont': 'VT'}

def print_func_header(var):
    print("\n" + "-" * 100)
    print(f'{var}...\n')

def describe_df(df, var):
    print(f'\n{var} dataset overview:')
    df.info()
    print(df.head())

    attr_type_list = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (list, np.ndarray, gpd.GeoDataFrame))).any()]
    print('\nattributes (data type - list):\n', attr_type_list)

    num_unique = df[[col for col in df.columns if col not in attr_type_list]].nunique()
    print('\ncount of unique values in each attribute (not list or np.ndarray):\n', num_unique)

    print(f'\n{var} dataset attributes:\n', df.columns.tolist())


def plot_helper(ids, df, dir, var, flowline=None):
    """
    Call this function to plot Sentinel-2 images grouped by id

    Args:
        ids : a list of ids
        df: The DataFrame selected
        dir: The directory to save plots
        var: part of plot name
        flowline: The GeoDataFrame of flowlines, if available
    """
    for current_id in ids:
        # Filter the data for the current id
        id_group = df[df['id'] == current_id]
        num_images = len(id_group)
        event_day = id_group['event_day'].iloc[0]
        
        # Create a figure for the current id
        fig, axes = plt.subplots(1, num_images, figsize=(4 * num_images, 5))
        fig.suptitle(f"ID: {current_id}\nEvent Day: {event_day}")

        if num_images == 1:
            axes = [axes]

        for j, (_, row) in enumerate(id_group.iterrows()):
            image_path = os.path.join(row['dir'], row['filename'])
            lat = row['latitude']
            lon = row['longitude']

            with rasterio.open(image_path) as src:
                tiff_crs = src.crs
                bounds = src.bounds

                show(src, ax=axes[j])
                
                if flowline is not None:
                    if flowline.crs != tiff_crs:
                        flowline = flowline.to_crs(tiff_crs)
                    
                    flowline.plot(ax=axes[j], color='cyan', linewidth=0.4)

                transformer = Transformer.from_crs("EPSG:4326", tiff_crs, always_xy=True)
                raster_x, raster_y = transformer.transform(lon, lat)
                axes[j].plot(raster_x, raster_y, 'ro', markersize=6, zorder=3)

                axes[j].set_title(f"Date: {row['date']}\nPeriod: {row['period']}")
                axes[j].set_xlim(bounds.left, bounds.right)
                axes[j].set_ylim(bounds.bottom, bounds.top)

        plt.tight_layout()
        plt.savefig(f"figs/{dir}/{current_id}_{var}.png")
        plt.close(fig)
        print(f"complete - {current_id}")

def apply_cloud_mask(image, cloud_mask_path):

    with rasterio.open(cloud_mask_path) as src:
        cloud_mask = src.read(1)

    valid_mask = cloud_mask == 0
    result = np.where(valid_mask, image, np.nan)

    return result

def read_ndwi_tif(file_path, threshold=-0.1):

    with rasterio.open(file_path) as src:
        ndwi_mask = src.read(1) 

    binary_water_mask = ndwi_mask > threshold

    return binary_water_mask