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

# reference - https://hydro.nationalmap.gov/arcgis/services/nhd/MapServer/WMSServer?request=GetCapabilities&service=WMS
def collect_nhd(layers, default_crs='EPSG:4326'):
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

        if gdf.crs is None:
            gdf.set_crs(default_crs, inplace=True)

        gdfs.append(gdf)
    return gdfs

# work when EPSG:4326 in collect_nhd function
tif_dir = 'data/img_s2/2023-07/45326_20230726T153819_20230726T153828_T18TXQ_VIS.tif'

# work when EPSG:4326 in collect_nhd function
tif_dir_1 = 'data/img_s2/2023-07/44929_20230706T153819_20230706T155055_T18TXN_VIS.tif'

# doesn't work when EPSG:4326 in collect_nhd function
tif_dir_2 = 'data/img_s2/2023-07/44909_20230706T153819_20230706T155055_T18TXP_VIS.tif'

tif_path = tif_dir_2
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
        if not gdf.empty:
            nhd_crs = gdf.crs
            if nhd_crs != tiff_crs:
                gdf = gdf.to_crs(tiff_crs)
            gdf.plot(ax=ax, color='blue', linewidth=1.5)

    ax.set_xlim(bounds.left, bounds.right)
    ax.set_ylim(bounds.bottom, bounds.top)
    plt.title(f' NHD Layers Over Sentinel-2 Imagery')

    # if testiing on tif_dir_1, save as test_1 (tif_dir_2, test_2)
    plt.savefig(f'figs/test/test_2.png')
    plt.close()  