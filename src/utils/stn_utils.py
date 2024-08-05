"""
This script includes the functions used to collect and preprocess flood event observations (high-water marks).

This file can be imported as a module and includes the following functions:
    * collect_stn - returns a DataFrame representing the collected high-water marks from URL;
    * preprocess_stn - returns a DataFrame representing the preprocessed high-water marks.
"""

# import libraries
import requests
import pandas as pd
from utils import global_utils

def collect_stn(area, filename):
    """
    Download high-water marks from STN database(https://stn.wim.usgs.gov/STNDataPortal/)
 
    Args:
        area (list of str): A list of names representing the areas of interest (e.g., ["ME", "VT"])
        filename (str): The file to be saved
 
    Returns:
        pd.DataFrame: A DataFrame containing the original high-water marks in the specified area
    """
    global_utils.print_func_header('step 1 - download high-water marks from STN flood event database')

    stn = []
    for i in area:
        # construct the URL for data retrieval
        stn_url = f"""https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=&
                      EventType=&EventStatus=0&States={i}&County=&HWMType=&HWMQuality=&
                      HWMEnvironment=&SurveyComplete=&StillWater="""
        
        # fetch the data from URL
        res = requests.get(stn_url)
        data = res.json()

        # convert to DataFrame and add to the list
        df_temp = pd.DataFrame(data)
        stn.append(df_temp)
        print(f'complete - {i} high-water marks')

    # combine into a single DataFrame
    df = pd.concat(stn, ignore_index=True)

    global_utils.describe_df(df, 'high water marks')

    # save to a CSV file
    df.to_csv(f'data/df_stn/{filename}.csv', index=False)
    return df

def preprocess_stn(df, attr_list, check_list, date_threshold, filename):
    """
    Preprocess the collected high-water marks 
 
    Args:
        df (pd.DataFrame): The original DataFrame representing high-water marks
        attr_list (list of str): A list of attributes to be selected
        check_list (list of str): A list of attributes used to identify unwanted observations
        date_threshold (int): The date used to filter the high-water marks
        filename (str): The file to be saved

    Returns:
        pd.DataFrame: A DataFrame representing the preprocessed high-water marks
    """
    global_utils.print_func_header('step 2 - preprocess the collected high-water marks')

    df_mod = df.copy()

    # rename the columns for simplicity
    df_mod = df_mod.rename(columns={'eventName': 'event', 
                            'stateName': 'state', 
                            'countyName': 'county', 
                            'hwm_id': 'id', 
                            'hwm_locationdescription': 'note'})

    # remove the ` County` suffix in 'county' column
    df_mod.loc[:, 'county'] = df_mod['county'].str.replace(' County', '') 

    # drop the observations sharing the same location and event name
    df_mod = df_mod.drop_duplicates(subset=check_list, keep='first')

    # select the flood event observations after the specified year threshold
    df_mod['year'] = df_mod['event'].str.extract(r'(\d{4})').astype(float)
    df_mod = df_mod[df_mod['year'] >= date_threshold].copy()

    # select the specified attributes
    df_mod = df_mod[attr_list].reset_index(drop=True)
    df_mod['source'] = 'stn'
    global_utils.describe_df(df_mod, 'preprocessed high-water marks')
    print(f'\nflood events in STN database ({date_threshold} - now):\n', df_mod['event'].unique())

    # save the modified DataFrame
    df_mod.to_csv(f'data/df_stn/{filename}.csv', index=False)

    return df_mod