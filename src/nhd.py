"""
This script is used to collect and explore National Hydrography Dataset for the specified states.
"""
# import libraries
import os
import time
import requests
import zipfile
import rasterio
import pandas as pd
from utils import global_utils
import geopandas as gpd
from rasterio.plot import show
import matplotlib.pyplot as plt

# track the runtime
start = time.time()
print('\nSTART - NHD DATA COLLECTION AND PLOTTING\n')

# identify the state to be selected
area_abbr_list = global_utils.area_abbr_list
df = pd.read_csv('data/s2.csv')
area_in_df = df['state'].unique().tolist()
area_list = [state for state, abbr in area_abbr_list.items() if abbr in area_in_df]
content_selected = ['Shape/NHDFlowline.shp', 'Shape/NHDFlowline.shx', 'Shape/NHDFlowline.dbf', 'Shape/NHDFlowline.prj']

# download and explore National Hydrography Dataset for the specified areas
global_utils.print_func_header('download NHD')
for i in area_list:
    url = f'https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/Shape/NHD_H_{i}_State_Shape.zip'
    dir = f'data/nhd/{i}'
    os.makedirs(dir, exist_ok=True)
    name = os.path.basename(url)
    file_path = os.path.join(dir, name)
    res = requests.get(url)
    with open(file_path, 'wb') as f:
        f.write(res.content)
    print(f'download NHD for {i} - {name}')

    # utilize the last file_path (if area_list > 1) to explore the files within the ZIP archive
    with zipfile.ZipFile(file_path, 'r') as z:
        contents = z.namelist()
        
        for item in content_selected:
            if item in contents:
                z.extract(item, dir)
                print(f'\nextract {i} {item}')

global_utils.print_func_header('list all contents within the ZIP archive')
print(contents)

def add_nhd_layer_s2(df, area):
    '''
    Add NHD flowline as one layer above Sentinel-2 imagery and plot the result for inspection

    Args:
        df (pd.DataFrame): The selected DataFrame used to add NHD flowline layer
        area (list of str): The specified area (state)

    Notes:
        Plots will be saved in figs/s2_nhd folder
    '''
    global_utils.print_func_header('add NHD flowline above Sentinel-2 and plot the result')
    for i in area:
        shp_path = f'data/nhd/{i}/Shape/NHDFlowline.shp'
        gdf = gpd.read_file(shp_path)

        i_abbr = area_abbr_list[i]
        df_i = df[df['state'] == i_abbr]
        df_i = df_i[df_i['period'] == 'during flood']
        for index, row in df_i.iterrows():
            tif_path = os.path.join(row['dir'], row['filename'])
            output_file = row['filename'].replace('_VIS.tif', '_NHD')
            with rasterio.open(tif_path) as src:
                tiff_crs = src.crs
                bounds = src.bounds

                fig, ax = plt.subplots(figsize=(10, 10))
                show(src, ax=ax)

                if gdf.crs != tiff_crs:
                    gdf = gdf.to_crs(tiff_crs)

                gdf.plot(ax=ax, color='blue', linewidth=1.0)

                ax.set_xlim(bounds.left, bounds.right)
                ax.set_ylim(bounds.bottom, bounds.top)
                plt.title(f"NHD Over S2: {row['filename']}, Event Day: {row['event_day']}")

                plt.savefig(f'figs/s2_nhd/{output_file}.png')
                plt.close()
            print(f"complete - {row['filename']}")


add_nhd_layer_s2(df, area_list)
print('\nCOMPLETE - NHD DATA COLLECTION AND PLOTTING\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')