"""
This script includes the functions used to collect and preprocess flood event observations 
(high-water levels above moderate flood stage) documented in USGS Water Data Service.

This file can be imported as a module and contains the following functions:
    * collect_gauge_list - returns a DataFrame representing the collected gauge lists;
    * collect_gauge_info - returns a DataFrame representing flood-relevant information for the gauges;
    * collect_water_level - returns a DataFrame representing the high-water levels (above the moderate flood stage value) for the gauges with 'usgs' ids;
    * preprocess_water_level - returns a DataFrame representing the cleaned high water-levels.
"""

# import libraries
import re
import time
import requests
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from utils import global_utils

def collect_gauge_list(area, filename):
    """
    Download gauge (real-time water-monitoring sites) list for specified areas from NOAA websites (e.g., https://hads.ncep.noaa.gov/charts/ME.shtml)
 
    Args:
        area (list of str): A list of names representing the areas of interest (e.g., ["ME", "VT"])
        filename (str): The file to be saved
        
    Returns:
        pd.DataFrame: A DataFrame representing the collected gauge lists with columns 'NWSLI' and 'Description'
    """
    global_utils.print_func_header('step 1 - download gauge (real-time water-monitoring sites) list')
    data = []

    for i in area:
        # construct the URL for the gauge list in each state
        url = f'https://hads.ncep.noaa.gov/charts/{i}.shtml'

        # fetch the list from URL
        res = requests.get(url)
        content = res.text
        soup = BeautifulSoup(content, 'html.parser')

        # extract the rows containing the gauge information
        rows = soup.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            nwsli = cells[0].get_text(strip=True)
            desc = cells[1].get_text(strip=True)
            data.append({'nwsli': nwsli, 'description': desc, 'state': i})

        print(f'complete - {i} gauge data')

    # convert the data to DataFrame
    df = pd.DataFrame(data)

    # clean the DataFrame by removing the empty value and drop duplicates
    df = df.replace('', pd.NA).dropna(subset=['nwsli'])
    df = df.reset_index(drop=True)
    df = df.drop_duplicates()

    global_utils.describe_df(df, 'gauge list')

    # save to a CSV file
    df.to_csv(f'data/df_gauge/{filename}.csv', index=False)

    return df

def collect_gauge_info(df, filename):
    """
    Collect and preprocess usgsid and flood-related information for gauges from NOAA (e.g., https://water.noaa.gov/gauges/ASTM1)
    
    The collected data includes attributes such as usgsid, latitude, longitude, state, county, flood stages (minor/moderate/major) and flood impacts

    Args:
        df (pd.DataFrame): The DataFrame representing the gauge lists
    
    Returns:
        pd.DataFrame: A DataFrame representing flood-relevant information for the gauges, including only those with 
                      non-empty 'moderate' flood stage and 'usgsid' values
    """
    global_utils.print_func_header('step 2 - download flood-related information for gauges')

    # set the keywords to collect the information
    keywords = ["USGSID", "Latitude", "Longitude", "State", "County", "minor", "moderate", "major", "FloodImpacts"]

    # store the collected result and track the gauges without a website
    data_all = []
    progress = None

    for _, row in df.iterrows():

        data = {}
        nwsli = row['nwsli']
        state = row['state']
        # track the progress
        if state != progress:
            if progress:
                print(f'complete - flood-related information for gauges in {progress}')
            progress = state

        # construct the URL for gauge information
        url = f'https://water.noaa.gov/gauges/{nwsli}'

        # fetch the data from URL
        res = requests.get(url)
        if res.status_code == 200:
            content = res.text
            for i in keywords:
                if i == "Latitude" or i == "Longitude":
                    pattern = r'"{variable}":\s*([0-9.-]+)'.format(variable=i)
                elif i == "FloodImpacts":
                    pattern = r'"FloodImpacts":\s*(\[[^\]]*\])'
                elif i == "USGSID":
                    pattern = r'"USGSID":\s*"(\d+)"'
                elif i == "State":
                    pattern = r'"State":\s*{\s*"Abbreviation":\s*"(\w+)",\s*"Name":\s*"([^"]+)"'
                elif i == "County":
                    pattern = r'"County":\s*"([^"]+)"'
                else:
                    pattern = r'"{variable}":\s*{{[^}}]*"value":\s*([\d.]+)'.format(variable=i)

                match = re.search(pattern, content)
                result = match.group(1) if match else None
                data[i.lower()] = result
                data["nwsli"] = nwsli
            data_all.append(data)
    
    if progress:
        print(f'complete - flood-related information for gauges in {progress}')

    # convert the data to DataFrame
    df = pd.DataFrame(data_all)

    # select the gauges with non-empty 'moderate' flood stage value and non-empty 'USGSID' value 
    df = df[df['moderate'].notnull() & df['usgsid'].notnull()].reset_index(drop=True)

    global_utils.describe_df(df, 'Guage info')

    # save to a CSV file
    df.to_csv(f'data/df_gauge/{filename}.csv', index=False)

    return df

def collect_water_level(df, date_threshold, filename, area):
    """
    Collect and preprocess real-time water level above moderate flood stage value for specified gauges from USGS Water Data Services 
    (e.g., https://waterdata.usgs.gov/monitoring-location/01049320/#parameterCode=00065&period=P7D&showMedian=false)
    
    Args:
        df (pd.DataFrame): The DataFrame representing flood-related information for gauges from NOAA
        date_threshold (str): The date to filter water levels
        filename (str): The file to be saved
        area (str): The area of interests (state)
    
    Returns:
        pd.DataFrame: A DataFrame representing the instances that the water level is above the moderate flood stage value for the gauges with 'USGIS' ids
    """
    global_utils.print_func_header(f'step 3 - download high-water levels in {area}')

    df_water = pd.DataFrame()
    col = ['agency_cd', 'usgsid', 'datetime', 'tz_cd', 'elev_ft', 'note']
    error = []
    df_size = len(df)

    for index, row in df.iterrows():
        threshold = pd.to_numeric(row['moderate'])
        id = row['usgsid']

        # construct the URL for data retrieval
        date_threshold
        url = f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites={id}&parameterCd=00065&startDT={date_threshold}T00:00:00.000-05:00&endDT=2024-05-23T23:59:59.999-04:00&siteStatus=all&format=rdb"
        # fetch the data from URL
        res = requests.get(url)
        if res.status_code == 200:
            data = StringIO(res.text)
            rows = 0
            while True:
                line = data.readline()
                if not line.startswith('#'):
                    break
                rows += 1
            data.seek(0)
            df_i = pd.read_csv(data, sep='\t', skiprows=rows, comment='#', dtype=object)
            df_i = df_i.drop(df_i.index[0])
            try:
                df_i.columns = col
                df_i['elev_ft'] = pd.to_numeric(df_i['elev_ft'], errors='coerce')
                df_i = df_i.dropna(subset=['datetime', 'elev_ft'])
                df_i['event_day'] = pd.to_datetime(df_i['datetime']).dt.date

                # filter the dataframe to keep only the rows where 'elev_ft' is the maximum for each 'event_day'
                df_i_filtered = df_i.loc[df_i.groupby('event_day')['elev_ft'].idxmax()]

                # filter the dataframe to keep only the rows where 'elev_ft' is above the threshold
                df_i_filtered = df_i_filtered[df_i_filtered['elev_ft'] >= threshold]

                # accumulate the results if df_i_filtered is not empty
                if not df_i_filtered.empty:
                    df_water = pd.concat([df_water, df_i_filtered])
            except ValueError:
                error.append(id)
        else:
            error.append(id)

        progress = ((index+1) / df_size) * 100
        print(f'complete - high-water level for gauge USGS {id}: {round(progress, 2)}%')

    # preprocess the water level data
    df = df.rename(columns={'floodimpacts': 'note'})
    df_raw = pd.merge(df_water[['usgsid', 'event_day', 'tz_cd', 'elev_ft']], df[['usgsid', 'latitude', 'longitude', 'nwsli', 'note', 'state', 'county']], on='usgsid', how='left')

    # save to a CSV file
    df_raw.to_csv(f'data/df_gauge/{filename}.csv', index=False)

    # sleep for 60 seconds to avoid hitting the server too frequently
    time.sleep(60)
    return df_raw

def preprocess_water_level(df, attr_list, filename):
    """
    Preprocess the collected high water levels above moderate flood stage
    
    Args:
        df (pd.DataFrame): The DataFrame representing the high water levels (above moderate flood stage)
        attr_list (list of str): A list of column names to be selected
    
    Returns:
        pd.DataFrame: A DataFrame representing the cleaned high water levels above moderate flood stage
    """
    print('--------------------------------------------------------------')
    print('Step 4 - Preprocess high water level above moderate flood stage value...\n')
    df_mod = df.copy()
    df_mod['event_day'] = pd.to_datetime(df_mod['event_day'], errors='coerce')
    df_mod['event'] = df_mod['event_day'].dt.to_period('M').astype(str)

    # select the specified attributes
    df_mod = df_mod[attr_list]
    df_mod['source'] = 'gauge'

    print('modified dataset overview:')
    df_mod.info()

    # save to a CSV file
    df_mod.to_csv(f'data/df_gauge/{filename}.csv', index=False)

    return df_mod
