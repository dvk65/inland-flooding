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
import rasterio
import geopandas as gpd
from pyproj import Transformer
from utils import global_utils
from rasterio.plot import show
import matplotlib.pyplot as plt

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
        gdf = gpd.read_file(shp_path)

        # filter the DataFrame for the current state's data during the flood event
        i_abbr = area_abbr_list[i]
        df_i = df[df['state'] == i_abbr]
        # df_i = df_i[df_i['period'] == 'during flood']
        for _, row in df_i.iterrows():

            # extract the location of the current observation (will be plotted)
            lat = row['latitude']
            lon = row['longitude']

            # open the Sentinel-2 image
            tif_path = os.path.join(row['dir'], row['filename'])
            output_file = row['filename'].replace('_VIS.tif', '_NHD')
            with rasterio.open(tif_path) as src:
                tiff_crs = src.crs # coordinate reference system of the TIFF (EPSG:32618)
                bounds = src.bounds # bounding box of the TIFF (e.g., BoundingBox(left=619740.0, bottom=4606360.0, right=631690.0, top=4618360.0))

                fig, ax = plt.subplots(figsize=(10, 10))

                # show the Sentinel-2 image
                show(src, ax=ax)

                # transform the GeoDataFrame's CRS (EPSG:4269) to match the TIFF CRS 
                if gdf.crs != tiff_crs:
                    gdf = gdf.to_crs(tiff_crs)

                gdf.plot(ax=ax, color='blue', linewidth=0.5)

                ax.set_xlim(bounds.left, bounds.right)
                ax.set_ylim(bounds.bottom, bounds.top)

                transformer = Transformer.from_crs("EPSG:4326", tiff_crs, always_xy=True)
                raster_x, raster_y = transformer.transform(lon, lat)
                ax.plot(raster_x, raster_y, 'ro', markersize=3, zorder=3)
                plt.title(f"NHD Over S2 - ID: {row['id']}, S2 Date:{row['date']}, Event Day: {row['event_day']}")

                plt.savefig(f'figs/s2_nhd/{output_file}.png')
                plt.close()
            print(f"complete - {row['filename']}")
