"""
This script includes the functions used as a module in multiple scripts.  

This file can be imported as a module and includes the following functions:
    * print_func_header - print a summary of the running function;
    * collect_nhd - returns a list of GeoDataFrames, each representing an NHD layer.

"""
# import libaries
import rasterio
import numpy as np
import geopandas as gpd

flood_event_periods = {'2021 Henri': ['2021-08-15', '2021-08-23'],
              '2018 March Extratropical Cyclone': ['2018-03-01', '2018-03-05'],
              '2018 January Extratropical Cyclone': ['2018-01-02', '2018-01-06'],
              '2023 July MA NY VT Flood': ['2023-07-10', '2023-07-11'],
              '2023 December East Coast Cyclone': ['2023-12-17', '2023-12-18']}

area_abbr_list = {'Connecticut': 'CT', 'Maine': 'ME', 
                  'Massachusetts': 'MA', 'New Hampshire': 'NH', 
                  'Rhode Island': 'RI', 'Vermont': 'VT'}

def print_func_header(var):
    print('-----------------------------------------------------------------------')
    print(f'{var}...\n')

def describe_df(df, var):
    print(f'\n{var} dataset overview:')
    df.info()
    print(df.head())

    attr_type_list = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, (list, np.ndarray, gpd.GeoDataFrame))).any()]
    print('\nattributes (data type - list):\n', attr_type_list)

    num_unique = df[[col for col in df.columns if col not in attr_type_list]].nunique()
    print('\ncount of unique values in each attribute (not list or np.ndarray):\n', num_unique)

# def read_tif(file_path):
#     with rasterio.open(file_path) as src:
#         return src.read(), src.profile