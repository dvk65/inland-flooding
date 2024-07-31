"""
This script currently tests NHD dataset layer on satellite imagery
"""
import os
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from rasterio.plot import show

# data downloading from https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_Vermont_State_Shape.zip (will neeed to be added in the project)
shp_path = 'data/nhd/NHD_H_Vermont_State_Shape/Shape/NHDFlowline.shp'
gdf = gpd.read_file(shp_path)

tif_paths = [
    'data/img_s2/2023-07/45326_20230726T153819_20230726T153828_T18TXQ_VIS.tif',
    'data/img_s2/2023-07/44929_20230706T153819_20230706T155055_T18TXN_VIS.tif',
    'data/img_s2/2023-07/44909_20230706T153819_20230706T155055_T18TXP_VIS.tif'
]

# convert gdf CRS to EPSG:4326 seems to be unnecessary?
# gdf = gdf.to_crs(epsg=4326)

count = 1
for tif_path in tif_paths:
    print(f"Processing: {tif_path}")
    with rasterio.open(tif_path) as src:
        tiff_crs = src.crs
        bounds = src.bounds

        fig, ax = plt.subplots(figsize=(10, 10))
        show(src, ax=ax)

        if gdf.crs != tiff_crs:
            gdf = gdf.to_crs(tiff_crs)

        gdf.plot(ax=ax, color='blue', linewidth=1.5)

        ax.set_xlim(bounds.left, bounds.right)
        ax.set_ylim(bounds.bottom, bounds.top)
        plt.title(f'NHD Over S2: {os.path.basename(tif_path)}')

        plt.savefig(f'figs/test/test_{count}.png')
        plt.close()
        count += 1