"""
This script includes the functions used to collect and preprocess flood event observations (high-water marks).

This file can be imported as a module and includes the following functions:
    * collect_stn - return a DataFrame representing the collected high-water marks from URL;
    * preprocess_stn - return a DataFrame representing the preprocessed high-water marks.
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

def preprocess_stn(df, attr_list, check_list, date_threshold, filename, explore=False):
    """
    Preprocess the collected high-water marks 
 
    Args:
        df (pd.DataFrame): The original DataFrame representing high-water marks
        attr_list (list of str): A list of attributes to be selected
        check_list (list of str): A list of attributes used to identify unwanted observations
        date_threshold (int): The date used to filter the high-water marks
        filename (str): The file to be saved
        explore (bool, optional): If True, the function will be used for exploration and the modified dataset will not be saved as CSV file. Default is False.

    Returns:
        pd.DataFrame: A DataFrame representing the preprocessed high-water marks
    """
    global_utils.print_func_header('step 2 - preprocess the collected high-water marks')

    df_mod = df.copy()

    # drop the attribute `files` storing hwm file (images) which is not downloaded using this approach
    df_mod = df_mod.drop(columns=['files'])

    # rename the columns for simplicity
    df_mod = df_mod.rename(columns={'eventName': 'event', 
                            'stateName': 'state', 
                            'countyName': 'county', 
                            'hwm_id': 'id', 
                            'hwm_locationdescription': 'note'})

    # drop duplicates using all attributes
    df_mod = df_mod.drop_duplicates(keep='first')
    global_utils.describe_df(df_mod, 'high-water marks after dropping duplicates using all attributes')

    # select the specified attributes
    df_mod = df_mod[attr_list]
    df_mod['source'] = 'stn'

    # remove the ` County` suffix in 'county' column
    df_mod.loc[:, 'county'] = df_mod['county'].str.replace(' County', '') 

    # check the duplicates 
    df_duplicates = df_mod[df_mod.duplicated(subset=check_list, keep=False)]
    print(f"\nduplicates in {check_list}:\n", df_duplicates)

    # examine the the duplicates by locating the original dataframe (difference in the attributes not selected)
    index_duplicates = df_duplicates.index
    sample_duplicates_check = index_duplicates[:4] # adjust the value based on the previous print result
    sample_duplicates_id = df_mod.loc[sample_duplicates_check, 'id'].values

    for i in range(len(sample_duplicates_id) - 1):  
        for j in range(i + 1, len(sample_duplicates_id)):  
            original_row = df[df['hwm_id'] == sample_duplicates_id[i]].iloc[0]
            duplicate_row = df[df['hwm_id'] == sample_duplicates_id[j]].iloc[0]
            result_compared = original_row.compare(duplicate_row)
            print(f"difference between id {sample_duplicates_id[i]} and id {sample_duplicates_id[j]}:\n", result_compared)

    # check unique flood events
    print(f'\nflood events in STN database:\n', df_mod['event'].unique().tolist())

    if not explore:
        # drop the unwanted duplicates after exploration
        df_mod = df_mod.drop_duplicates(subset=check_list, keep='first')

        # select the flood event observations after the specified year threshold
        df_mod['year'] = df_mod['event'].str.extract(r'(\d{4})').astype(float)
        df_mod = df_mod[df_mod['year'] >= date_threshold]
        df_mod = df_mod.drop(columns = ['year']).reset_index(drop=True)

        # save the modified DataFrame
        df_mod.to_csv(f'data/df_stn/{filename}.csv', index=False)

    global_utils.describe_df(df_mod, 'preprocessed high-water marks')

    return df_mod