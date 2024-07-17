import pandas as pd
import requests

# download STN flood event data - New England Region
def stn_data_collect(area):
    stn = []
    for i in area:
        stn_url = f'https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=&EventType=&EventStatus=0&States={i}&County=&HWMType=&HWMQuality=&HWMEnvironment=&SurveyComplete=&StillWater='
        stn_res = requests.get(stn_url)
        data = stn_res.json()
        temp_df = pd.DataFrame(data)
        stn.append(temp_df)

    df = pd.concat(stn, ignore_index=True)
    df = df.rename(columns={'eventName': 'event', 'stateName': 'state', 'countyName': 'county', 'hwm_id': 'id'})
    df.loc[:, 'county'] = df['county'].str.replace(' County', '') 
    df.to_csv('data/stn/stn_flood_event_raw.csv', index=False)
    return df

# preprocess STN flood event data
def stn_data_prep(df, attr_list, duplicate_check):

    # select recent flood events (when Landsat 8 imagery becomes available)
    print('\nFlood Events in STN Database:\n', df['event'].unique())
    df['year'] = df['event'].str.extract(r'(\d{4})').astype(float)
    df_mod = df[df['year'] >= 2013].copy()
    print('\nFlood Events in STN Database (2013 - now):\n', df_mod['event'].unique())

    # select the attributes
    df_mod = df_mod[attr_list]

    # drop duplicate values
    df_mod = df_mod.drop_duplicates(subset=duplicate_check, keep='first')

    # save the modified version
    df_mod.to_csv('data/stn/stn_flood_event_mod.csv', index=False)

    return df_mod