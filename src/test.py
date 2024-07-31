"""
This script currently tests NHD dataset layer on satellite imagery
"""
import os
import requests
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
from rasterio.plot import show
from shapely.geometry import shape

def collect_nhd(layers, default_crs='EPSG:32618'):
    """
    Collect and return NHD (National Hydrography Dataset) layers as GeoDataFrames (https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer)

    Alternative approach: https://apps.nationalmap.gov/downloader/
    Args:
        layers (list): A list of layers to be collected from the NHD dataset.
        default_crs (str): The CRS to set
    
    Returns:
        list: A list of GeoDataFrames, each representing an NHD layer.  
    """
    root_url = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/{}/query'
    gdfs = []
    for layer in layers:
        url = root_url.format(layer)
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        res = requests.get(url, params=params)
        data = res.json()
        features = data['features']
        geo = [shape(feature['geometry']) for feature in features]
        properties = [feature['properties'] for feature in features]
        gdf = gpd.GeoDataFrame(properties, geometry=geo)

        gdf.set_crs(default_crs, inplace=True)

        gdfs.append(gdf)
    return gdfs

tif_dir = 'data/img_s2/2023-07/'

for file_name in os.listdir(tif_dir)[:10]:
    tif_path = os.path.join(tif_dir, file_name)
    print(f"current - {tif_path}")

    with rasterio.open(tif_path) as src:
        tiff_crs = src.crs
        bounds = src.bounds  
        
        fig, ax = plt.subplots(figsize=(10, 10))
        show(src, ax=ax)

        # nhd flowline - 4, 5, 6 (currently test all for debugging)
        nhd_layers = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        nhd_gdfs = collect_nhd(nhd_layers)

        for i, gdf in enumerate(nhd_gdfs):
            gdf.plot(ax=ax, color='blue', linewidth=2.0)

        ax.set_xlim(bounds.left, bounds.right)
        ax.set_ylim(bounds.bottom, bounds.top)
        plt.title(f'{file_name} NHD Layers Over Sentinel-2 Imagery')

        plt.savefig(f'figs/test/{file_name}.png')
        plt.close()  