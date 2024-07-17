# import libraries
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO

# collect and preprocess gauge list
def nwsli_data_collect(area):
    nwsli_data = []

    # collect gauge list in each state
    for i in area:
        nwsli_url = f'https://hads.ncep.noaa.gov/charts/{i}.shtml'
        nwsli_res = requests.get(nwsli_url)
        nwsli_list = nwsli_res.text
        nwsli_soup = BeautifulSoup(nwsli_list, 'html.parser')
        nwsli_rows = nwsli_soup.find_all('tr')
        for row in nwsli_rows[1:]:
            cells = row.find_all('td')
            nwsli = cells[0].get_text(strip=True)
            loc_desc = cells[1].get_text(strip=True)
            nwsli_data.append({'NWSLI': nwsli, 'Dscription': loc_desc})

    nwsli_list = pd.DataFrame(nwsli_data)
    nwsli_list = nwsli_list.replace('', pd.NA).dropna(how='all')
    nwsli_list = nwsli_list.reset_index(drop=True)
    nwsli_list = nwsli_list.drop_duplicates()
    nwsli_list.to_csv('data/gauge/gauge_nwsli_list.csv', index=False)

    return nwsli_list

# collect flood stage information from NOAA
def flood_stage(df):
    noaa_keywords = ["USGSID", "Latitude", "Longitude", "State", "County", "minor", "moderate", "major", "FloodImpacts"]
    noaa_result_list = []
    na_list = []
    for index, row in df.iterrows():
        noaa_result = {}
        nwsli_id = row['NWSLI']
        gauge_url = f'https://water.noaa.gov/gauges/{nwsli_id}'
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

    flood_stage = pd.DataFrame(noaa_result_list)
    flood_stage_moderate = flood_stage[flood_stage['moderate'].notnull() & flood_stage['USGSID'].notnull()]
    flood_stage_moderate.to_csv('data/gauge/gauge_flood_stage_moderate.csv', index=False)

    return flood_stage_moderate

def extract_water_level(df):
    water_level_df = pd.DataFrame()
    water_level_col = ['agency_cd', 'usgsid', 'datetime', 'tz_cd', 'elev_ft', 'note']
    water_level_error = []
    for index, row in df.iterrows():
        threshold = pd.to_numeric(row['moderate'])
        id = row['USGSID']
        water_level_url = f"https://nwis.waterservices.usgs.gov/nwis/iv/?sites={id}&parameterCd=00065&startDT=2013-03-18T00:00:00.000-05:00&endDT=2024-05-23T23:59:59.999-04:00&siteStatus=all&format=rdb"
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

    # preprocess the water level data
    df = df.rename(columns={'USGSID': 'usgsid'})
    gauge_flood_event_raw = pd.merge(water_level_df[['usgsid', 'datetime', 'tz_cd', 'elev_ft']], df[['usgsid', 'Latitude', 'Longitude', 'nwsli_id', 'FloodImpacts', 'State', 'County']], on='usgsid', how='left')
    gauge_flood_event_raw['id'] = gauge_flood_event_raw['nwsli_id'] + '_' + gauge_flood_event_raw.index.astype(str) 
    gauge_flood_event_raw = gauge_flood_event_raw.rename(columns={'Latitude': 'latitude', 'Longitude': "longitude", 'State': 'state', 'County': 'county'})
    gauge_flood_event_raw.to_csv('data/gauge/gauge_flood_event_raw.csv', index=False)
    return gauge_flood_event_raw

def prep_water_level(df, attr_list, duplicate_check):
    gauge_flood_event_mod = df[['id', 'datetime', 'state', 'county', 'latitude', 'longitude']].copy()
    gauge_flood_event_mod['datetime'] = pd.to_datetime(gauge_flood_event_mod['datetime'])
    gauge_flood_event_mod['event_day'] = gauge_flood_event_mod['datetime'].dt.strftime('%Y-%m-%d')
    gauge_flood_event_mod['event'] = gauge_flood_event_mod['datetime'].dt.to_period('M').astype(str)
    gauge_flood_event_mod = gauge_flood_event_mod[attr_list]
    gauge_flood_event_mod = gauge_flood_event_mod.drop_duplicates(subset=duplicate_check, keep='first')

    gauge_flood_event_mod.to_csv('data/gauge/gauge_flood_event_mod.csv', index=False)

    return gauge_flood_event_mod
