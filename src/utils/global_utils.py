"""
This script includes the functions used as a module in multiple scripts.  

This file can be imported as a module and includes the following functions:
    * print_func_header - print a summary of the running function;
    * describe_df - print an overview of the dataframe;
    * plot_helper - plot images grouped by id;
    * apply_cloud_mask - return a image with apply cloud mask by assigning NaN to cloud ans shadow pixels;
    * read_ndwi_tif - return the NDWI mask;
    * str_to_list - return a list of float numbers converted from a string representation.
"""
# import libaries
import os
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.plot import show
from pyproj import Transformer
import matplotlib.pyplot as plt

# flood event periods for STN high-water marks
flood_event_periods = {'2021 Henri': ['2021-08-15', '2021-08-23'],
              '2018 March Extratropical Cyclone': ['2018-03-01', '2018-03-05'],
              '2018 January Extratropical Cyclone': ['2018-01-02', '2018-01-06'],
              '2023 July MA NY VT Flood': ['2023-07-10', '2023-07-11'],
              '2023 December East Coast Cyclone': ['2023-12-17', '2023-12-18']}

# new england state list
area_abbr_list = {'Connecticut': 'CT', 'Maine': 'ME', 
                  'Massachusetts': 'MA', 'New Hampshire': 'NH', 
                  'Rhode Island': 'RI', 'Vermont': 'VT'}

def print_func_header(var):
    """
    Print a header at the beginning of a function to clearly mark the start of a function's execution
    Args:
        var (str): a short description of the function
    """
    print("\n" + "-" * 100)
    print(f'{var}...\n')

def describe_df(df, var):
    """
    Print an overview of the dataframe

    Args:
        df (pd.DataFrame): The dataframe to be checked
        var (str): The description of the dataframe
    """
    print(f'\n{var} dataset overview:')
    df.info()
    print(df.head())

    # exclude attributes with data type == list, np.ndarray, gpd.GeoDataFrame
    attr_type_list = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (list, np.ndarray, gpd.GeoDataFrame))).any()]
    print('\nattributes (data type - list):\n', attr_type_list)

    # print the number of unique values in each attribute
    num_unique = df[[col for col in df.columns if col not in attr_type_list]].nunique()
    print('\ncount of unique values in each attribute (not list or np.ndarray or gpd.GeoDataFrame):\n', num_unique)

    print(f'\n{var} dataset attributes:\n', df.columns.tolist())

def plot_helper(ids, df, dir, flowline=None):
    """
    Plot images grouped by id

    Args:
        ids : a list of ids
        df: The DataFrame selected
        dir: The directory to save plots
        flowline: The GeoDataFrame of flowlines, if available
    """
    for current_id in ids:

        # filter the data for the current id
        id_group = df[df['id'] == current_id]
        num_images = len(id_group)
        event_day = id_group['event_day'].iloc[0]
        
        # create a figure for the current id
        fig, axes = plt.subplots(1, num_images, figsize=(4 * num_images, 5))
        fig.suptitle(f"ID: {current_id}\nEvent Day: {event_day}")

        # check if only one image exists
        if num_images == 1:
            axes = [axes]

        for j, (_, row) in enumerate(id_group.iterrows()):
            image_path = os.path.join(row['dir'], row['filename'])
            lat = row['latitude']
            lon = row['longitude']

            # open the GeoTIFF
            with rasterio.open(image_path) as src:
                tiff_crs = src.crs
                bounds = src.bounds

                show(src, ax=axes[j])
                
                # convert the crs if using flowline
                if flowline is not None:
                    if flowline.crs != tiff_crs:
                        flowline = flowline.to_crs(tiff_crs)
                    
                    flowline.plot(ax=axes[j], color='cyan', linewidth=0.4)

                # add the flood event observation location as a red dot
                transformer = Transformer.from_crs("EPSG:4326", tiff_crs, always_xy=True)
                raster_x, raster_y = transformer.transform(lon, lat)
                axes[j].plot(raster_x, raster_y, 'ro', markersize=6, zorder=3)

                axes[j].set_title(f"Date: {row['date']}\nPeriod: {row['period']}")
                axes[j].set_xlim(bounds.left, bounds.right)
                axes[j].set_ylim(bounds.bottom, bounds.top)

        plt.tight_layout()
        plt.savefig(f"figs/{dir}/{row['id']}_{row['date']}_{dir}.png")
        plt.close(fig)
        print(f"complete - {current_id}")

def apply_cloud_mask(image, cloud_mask_path):
    """
    Apply cloud mask to a image by assigning cloud and shadow areas with NaN

    Args:
        image (np.ndarray): The input image
        cloud_mask_path (str): The file path to the cloud mask file
    
    Returns:
        np.ndarray: The array with cloud and shadow pixels set to NaN
    """
    # open the cloud mask
    with rasterio.open(cloud_mask_path) as src:
        cloud_mask = src.read(1)

    # set cloud and shadow pixels to NaN
    valid_mask = cloud_mask == 0
    result = np.where(valid_mask, image, np.nan)

    return result

def read_ndwi_tif(file_path, threshold=-0.1):
    """
    Create a water mask using NDWI GeoTIFF

    Args:
        file_path (str): The file path to the NDWI file
        threshold (float): The NDWI threshold used to distinguish water from non-water areas
    
    Returns:
        np.ndarray: A array where water areas are set to 1 and non-water areas are set to 0

    Notes:
        The selection of threshold is included in eda_s2.py. -0.1 is selected after testing different values on images
    """
    # open the NDWI file
    with rasterio.open(file_path) as src:
        ndwi_mask = src.read(1) 

    # create a water mask based on the threshold
    water_mask = np.where(ndwi_mask > threshold, 1, 0)

    return water_mask

def str_to_list(data):
    """
    Convert a string representation of a list into a list

    Args:
        data (str): The string representing a list

    Returns:
        list: A list of float values
    """
    return [float(x) for x in data.strip("[]").split(", ")]