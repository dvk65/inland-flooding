"""
This script is used to implement some experiments.
"""

import os
import rasterio
import pandas as pd
import geopandas as gpd
from rasterio.plot import show
import matplotlib.pyplot as plt
from utils import kmeans_utils

# load the image metadata dataframe
df = pd.read_csv('data/s2.csv')

# test flowline using the first row in the dataframe
for _, row in df[:1].iterrows():

    # read the image information
    image_path = os.path.join(row['dir'], row['filename'])
    _, sat_bounds, tiff_crs, _, _ = kmeans_utils.read_tif(image_path)
    
    area = 'Vermont' # hard-coded value (be careful if changing the row)

    # load the shapefile
    shp_path = f'data/nhd/{area}/Shape/NHDFlowline.shp'
    flowline = gpd.read_file(shp_path)
    
    # view flowline features
    print(flowline.columns)
    print(flowline['ftype'].unique().tolist())
    print(flowline['fcode'].unique().tolist())
    print(flowline['gnis_name'].unique().tolist())
    # major_rivers = flowline[(flowline['ftype'].isin(major_river)) & (flowline['lengthkm'] >= 0.6)]
    
    # convert crs
    if flowline.crs != tiff_crs:
        flowline = flowline.to_crs(tiff_crs)
    
    # plot the 
    fig, ax = plt.subplots(figsize=(10, 10))
    with rasterio.open(image_path) as src:
        show(src, ax=ax, title=f"s2 with flowline - ID: {row['id']}, Date: {row['date']}")
    
    flowline.plot(ax=ax, color='cyan', linewidth=0.5)
    
    ax.set_xlim(sat_bounds.left, sat_bounds.right)
    ax.set_ylim(sat_bounds.bottom, sat_bounds.top)
    
    plt.tight_layout()
    plt.savefig('figs/flowline_no_filter.png')
    plt.close()


# PCA demonstration - image reconstruction