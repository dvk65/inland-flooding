"""
This script includes the functions used to collect and preprocess flood events 
(high water levels above moderate flood stage) documented in USGS Water Data Service.

This file can be imported as a module and contains the following functions:
    * collect_gauge_list - returns a DataFrame representing the collected gauge lists with columns 'NWSLI' and 'Description'.
    * collect_gauge_info - returns a DataFrame representing flood-relevant information for the gauges.
    * collect_water_level - returns a DataFrame representing the high water levels (above the moderate flood stage value) for the gauges with 'USGIS' ids.
    * preprocess_water_level - returns a DataFrame representing the cleaned high water levels above moderate flood stage.
"""

# import libraries
import pandas as pd

import re
import requests
from io import StringIO
from bs4 import BeautifulSoup

def collect_gauge_list(area):
    """
    Download gauge (real-time water-monitoring sites) list for specified areas from NOAA websites (e.g., https://hads.ncep.noaa.gov/charts/ME.shtml)
 
    Args:
        area (list of str): A list of names representing the areas of interest (e.g., ["ME", "VT"]). 
 
    Returns:
        pd.DataFrame: A DataFrame representing the collected gauge lists with columns 'NWSLI' and 'Description'.
    """
    print('--------------------------------------------------------------')
    print('Step 1 - Download gauge (real-time water-monitoring sites) list for the New England Region...\n')
    gauge_data = []

    for i in area:
        # construct the URL for the gauge list in each state
        gauge_url = f'https://hads.ncep.noaa.gov/charts/{i}.shtml'

        # fetch the list from URL
        gauge_res = requests.get(gauge_url)
        gauge_list = gauge_res.text
        gauge_soup = BeautifulSoup(gauge_list, 'html.parser')

        # extract the rows containing the gauge information
        gauge_rows = gauge_soup.find_all('tr')
        for row in gauge_rows[1:]:
            cells = row.find_all('td')
            nwsli = cells[0].get_text(strip=True)
            loc_desc = cells[1].get_text(strip=True)
            gauge_data.append({'NWSLI': nwsli, 'Dscription': loc_desc, 'State': i})

        print(f'complete - {i} gauge data')

    # convert the data to DataFrame
    df_gauge_list = pd.DataFrame(gauge_data)

    # clean the DataFrame by removing the empty value and drop duplicates
    df_gauge_list = df_gauge_list.replace('', pd.NA).dropna(subset=['NWSLI'])
    df_gauge_list = df_gauge_list.reset_index(drop=True)
    df_gauge_list = df_gauge_list.drop_duplicates()

    print('\ndataset overview:')
    df_gauge_list.info()

    # save to a CSV file
    df_gauge_list.to_csv('data/df_gauge/df_gauge_list.csv', index=False)

    return df_gauge_list

def collect_gauge_info(df):
    """
    Retrieve the USGSID and flood-related information for gauges from NOAA (e.g., https://water.noaa.gov/gauges/ASTM1).
    
    The collected data includes attributes such as USGSID, latitude, longitude, state, county, flood stages (minor, moderate, major) and flood impacts.

    Args:
        df (pd.DataFrame): The DataFrame representing the gauge lists with columns 'NWSLI' and 'Description'.
    
    Returns:
        pd.DataFrame: A DataFrame representing flood-relevant information for the gauges, including only those with 
                      non-empty 'moderate' flood stage and 'USGSID' values.
    """
    print('--------------------------------------------------------------')
    print('Step 2 - Download flood-related information for gauges from NOAA...\n')

    # set the keywords to collect the information
    noaa_keywords = ["USGSID", "Latitude", "Longitude", "State", "County", "minor", "moderate", "major", "FloodImpacts"]

    # store the collected result and track the gauges without a website
    noaa_result_list = []
    na_list = []
    progress_check = None

    for index, row in df.iterrows():

        noaa_result = {}
        nwsli_id = row['NWSLI']
        state = row['State']
        # track the progress
        if state != progress_check:
            if progress_check:
                print(f'complete - flood-related information for gauges in {progress_check}')
            progress_check = state

        # construct the URL for gauge information
        gauge_url = f'https://water.noaa.gov/gauges/{nwsli_id}'

        # fetch the data from URL
        noaa_res = requests.get(gauge_url)
        if noaa_res.status_code == 200:
            noaa_content = noaa_res.text
            for i in noaa_keywords:
                if i == "Latitude" or i == "Longitude":
                    noaa_pattern = r'"{variable}":\s*([0-9.-]+)'.format(variable=i)
                elif i == "FloodImpacts":
                    noaa_pattern = r'"FloodImpacts":\s*(\[[^\]]*\])'
                elif i == "USGSID":
                    noaa_pattern = r'"USGSID":\s*"(\d+)"'
                elif i == "State":
                    noaa_pattern = r'"State":\s*{\s*"Abbreviation":\s*"(\w+)",\s*"Name":\s*"([^"]+)"'
                elif i == "County":
                    noaa_pattern = r'"County":\s*"([^"]+)"'
                else:
                    noaa_pattern = r'"{variable}":\s*{{[^}}]*"value":\s*([\d.]+)'.format(variable=i)

                noaa_match = re.search(noaa_pattern, noaa_content)
                noaa_collected = noaa_match.group(1) if noaa_match else None
                noaa_result[i] = noaa_collected
                noaa_result["nwsli_id"] = nwsli_id
            noaa_result_list.append(noaa_result)
        else:
            na_list.append(nwsli_id)
    
    if progress_check:
        print(f'complete - flood-related information for gauges in {progress_check}')

    # convert the data to DataFrame
    df_gauge_info = pd.DataFrame(noaa_result_list)

    # select the gauges with non-empty 'moderate' flood stage value and non-empty 'USGSID' value 
    df_gauge_info = df_gauge_info[df_gauge_info['moderate'].notnull() & df_gauge_info['USGSID'].notnull()]

    print('\ndataset overview:')
    df_gauge_info.info()

    # save to a CSV file
    df_gauge_info.to_csv('data/df_gauge/df_gauge_info.csv', index=False)

    return df_gauge_info

def collect_water_level(df):
    """
    Retrieve real-time water level above moderate flood stage value for specified gauges from USGS Water Data Services (e.g., https://waterdata.usgs.gov/monitoring-location/01049320/#parameterCode=00065&period=P7D&showMedian=false).
    
    Args:
        df (pd.DataFrame): The DataFrame representing flood-related information for gauges from NOAA
    
    Returns:
        pd.DataFrame: A DataFrame representing the instances that the water level is above the moderate flood stage value for the gauges with 'USGIS' ids
    """
    print('--------------------------------------------------------------')
    print('Step 3 - Download high water level (above moderate flood stage) from USGS Water Data Services...\n')
    water_level_df = pd.DataFrame()
    water_level_col = ['agency_cd', 'usgsid', 'datetime', 'tz_cd', 'elev_ft', 'note']
    water_level_error = []
    df = df.reset_index(drop=True)
    df_size = len(df)

    for index, row in df.iterrows():
        threshold = pd.to_numeric(row['moderate'])
        id = row['USGSID']
        # construct the URL for data retrieval
        water_level_url = f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites={id}&parameterCd=00065&startDT=2017-03-28T00:00:00.000-05:00&endDT=2024-05-23T23:59:59.999-04:00&siteStatus=all&format=rdb"
        # fetch the data from URL
        water_level_res = requests.get(water_level_url)
        if water_level_res.status_code == 200:
            water_level_data = StringIO(water_level_res.text)
            header_rows = 0
            while True:
                line = water_level_data.readline()
                if not line.startswith('#'):
                    break
                header_rows += 1
            water_level_data.seek(0)
            water_level_df_i = pd.read_csv(water_level_data, sep='\t', skiprows=header_rows, comment='#', dtype=object)
            water_level_df_i = water_level_df_i.drop(water_level_df_i.index[0])
            try:
                water_level_df_i.columns = water_level_col
                water_level_df_i.iloc[:, 4] = pd.to_numeric(water_level_df_i.iloc[:, 4], errors='coerce')

                fitered_water_level_df = water_level_df_i[water_level_df_i.iloc[:, 4] >= threshold]
                if not fitered_water_level_df.empty:
                    water_level_df = pd.concat([water_level_df, fitered_water_level_df])
            except ValueError:
                water_level_error.append(id)
        else:
            water_level_error.append(id)

        progress = ((index+1) / df_size) * 100
        print(f'complete - high water level (above moderate flood stage) for gauge USGS {id}: {round(progress, 2)}%')


    # preprocess the water level data
    df = df.rename(columns={'USGSID': 'usgsid', 'FloodImpacts': 'note'})
    df_gauge_raw = pd.merge(water_level_df[['usgsid', 'datetime', 'tz_cd', 'elev_ft']], df[['usgsid', 'Latitude', 'Longitude', 'nwsli_id', 'note', 'State', 'County']], on='usgsid', how='left')
    df_gauge_raw['id'] = df_gauge_raw['nwsli_id'] + '_' + df_gauge_raw.index.astype(str) 
    df_gauge_raw = df_gauge_raw.rename(columns={'Latitude': 'latitude', 'Longitude': "longitude", 'State': 'state', 'County': 'county'})
    print('\ndataset overview:')
    df_gauge_raw.info()

    # save to a CSV file
    df_gauge_raw.to_csv('data/df_gauge/df_gauge_raw.csv', index=False)
    return df_gauge_raw

def preprocess_water_level(df, attr_list, duplicate_check):
    """
    Preprocess the collected high water levels above moderate flood stage
    
    Args:
        df (pd.DataFrame): The DataFrame representing the high water levels (above moderate flood stage)
        attr_list (list of str): A list of column names to be selected.
        duplicate_check (list of str): A list of column names to identify duplicate rows.
    
    Returns:
        pd.DataFrame: A DataFrame representing the cleaned high water levels above moderate flood stage
    """
    print('--------------------------------------------------------------')
    print('Step 4 - Preprocess high water level above moderate flood stage value...\n')
    df_mod = df.copy()
    df_mod['datetime'] = pd.to_datetime(df_mod['datetime'])
    df_mod['event_day'] = df_mod['datetime'].dt.strftime('%Y-%m-%d')
    df_mod['event'] = df_mod['datetime'].dt.to_period('M').astype(str)

    # select the specified attributes
    df_mod = df_mod[attr_list]

    # drop the instances with the same location and event name
    df_mod = df_mod.drop_duplicates(subset=duplicate_check, keep='first')

    print('modified dataset overview:')
    df_mod.info()

    # save to a CSV file
    df_mod.to_csv('data/df_gauge/df_gauge_mod.csv', index=False)

    return df_mod
