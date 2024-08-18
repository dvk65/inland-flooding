"""
This script is used to implement some experiments.
"""

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
# for _, row in df[:2].iterrows():
row = df.iloc[1]
# read the image information
image_path = os.path.join(row['dir'], row['filename'])
_, sat_bounds, tiff_crs, _, _ = kmeans_utils.read_tif(image_path)

area = 'Vermont' # hard-coded value (be careful if changing the row)

# load the shapefile
shp_path = f'data/nhd/{area}/Shape/NHDFlowline.shp'
flowline = gpd.read_file(shp_path)

vaa_path = f'data/nhd/{area}/Shape/NHDFlowlineVAA.dbf'
flowline_vaa = gpd.read_file(vaa_path)

flowline_combined = flowline.merge(flowline_vaa[['permanent_', 'streamorde', 'streamleve']], on='permanent_')
major_rivers = flowline_combined[flowline_combined['streamorde'] >= 5]

# convert crs
if major_rivers.crs != tiff_crs:
    major_rivers = major_rivers.to_crs(tiff_crs)

# plot 
fig, ax = plt.subplots(figsize=(10, 10))
with rasterio.open(image_path) as src:
    show(src, ax=ax, title=f"s2 with flowline - ID: {row['id']}, Date: {row['date']}")

major_rivers.plot(ax=ax, color='cyan', linewidth=0.5)

ax.set_xlim(sat_bounds.left, sat_bounds.right)
ax.set_ylim(sat_bounds.bottom, sat_bounds.top)

plt.tight_layout()
plt.show()


# PCA demonstration - image reconstruction
