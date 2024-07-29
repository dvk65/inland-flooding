"""
This script includes the functions used to collect and preprocess flood events (high water marks) documented in STN Data Portal.

This file can be imported as a module and contains the following functions:
    * collect_stn - returns a DataFrame representing the collected high water mark data.
    * preprocess_stn - returns a DataFrame representing the modified high water mark data.
"""
# import libraries
import requests

import pandas as pd

def collect_stn(area):
    """
    Download high water mark data from STN database(https://stn.wim.usgs.gov/STNDataPortal/)
 
    Args:
        area (list of str): A list of names representing the areas of interest (e.g., ["ME", "VT"]). 
 
    Returns:
        pd.DataFrame: A DataFrame containing the collected high water mark data.
    """
    print('--------------------------------------------------------------')
    print('Step 1 - Download high water marks from STN flood event database...\n')
    stn = []

    for i in area:
        # construct the URL for data retrieval
        stn_url = f"""https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=&
                      EventType=&EventStatus=0&States={i}&County=&HWMType=&HWMQuality=&
                      HWMEnvironment=&SurveyComplete=&StillWater="""
        
        # fetch the data from URL
        res = requests.get(stn_url)
        data = res.json()

        # conver JSON data to DataFrame and add to the list
        temp_df = pd.DataFrame(data)
        stn.append(temp_df)
        print(f'complete - {i} high water mark data')

    # combine all DataFrames into a single DataFrame
    df = pd.concat(stn, ignore_index=True)

    # rename the columns for simplicity
    df = df.rename(columns={'eventName': 'event', 
                            'stateName': 'state', 
                            'countyName': 'county', 
                            'hwm_id': 'id', 
                            'hwm_locationdescription': 'note'})

    # remove the ` County` suffix in 'county' column
    df.loc[:, 'county'] = df['county'].str.replace(' County', '') 

    print('\ndataset overview:')
    df.info()

    # save to a CSV file
    df.to_csv('data/df_stn/df_stn_raw.csv', index=False,  quotechar='"')
    return df

def preprocess_stn(df, attr_list, duplicate_check):
    """
    Preprocess the collected high water mark data to filter and clean the dataset.
 
    Args:
        df (pd.DataFrame): The original DataFrame representing high water mark data.
        attr_list (list of str): A list of column names to be selected.
        duplicate_check (list of str): A list of column names used to identify duplicate rows.

    Returns:
        pd.DataFrame: A DataFrame representing the modified high water mark data.
    """
    print('--------------------------------------------------------------')
    print('Step 2 - Preprocess the collected high water mark data...\n')

    df_mod = df.copy()

    # drop the instances with the same location and event name
    df_mod = df_mod.drop_duplicates(subset=duplicate_check, keep='first')

    # select recent flood events (when Sentinel 2 imagery becomes available)
    df_mod['year'] = df_mod['event'].str.extract(r'(\d{4})').astype(float)
    df_mod = df_mod[df_mod['year'] >= 2017].copy()

    # select the specified attributes
    df_mod = df_mod[attr_list]

    print('modified dataset overview:')
    df_mod.info()

    print('\nflood events in STN database (2017 - now):\n', df_mod['event'].unique())

    # save the modified DataFrame
    df_mod.to_csv('data/df_stn/df_stn_mod.csv', index=False)

    return df_mod