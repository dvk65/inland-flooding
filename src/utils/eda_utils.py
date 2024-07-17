from shapely.geometry import Point, shape
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import seaborn as sns
import requests
import os
import re

# describe dataset
def desc_data(df):
    unique_count = df.nunique()
    print('Attribute Summary:\n')
    df.info()
    print('\nNumber of Unique Values in Each Attribute:\n', unique_count)

# count by group
def count_by_group(df, var):
    var_group = df.groupby(by=[var]).size().sort_values(ascending=False).to_frame(name='total_count')
    print(f'\nFlood Events Group By {var}:\n', var_group)

# visualize flood event by state
def plot_bar(df, var):
    plt.figure(figsize=(14, 10))
    plt.title(f'{var} - Flood Events by State')
    plt.xlabel('State')
    plt.ylabel('Flood Events')
    ax = sns.countplot(df, x='state', hue='event')
    for i in ax.containers:
        ax.bar_label(i,)
    plt.savefig(f'figs/{var}_event_count.png')
    plt.close()

# convert the event column in stn
def convert_date(stn):
    date_stn = stn['event'].str.extract(r'(\d{4}) (\w+)').drop_duplicates().reset_index()
    print('Flood Event Date in STN:\n', date_stn)    
    date_stn_mod = pd.to_datetime(date_stn.apply(lambda x: f"{x[0]} {x[1]}", axis=1), format='%Y %B', errors='coerce')
    date_stn_mod = date_stn_mod.dt.strftime('%Y-%m')
    print('Flood Event Date in STN (modified):\n', date_stn_mod)
    return date_stn_mod

# check the overlap between stn and gauge
def check_overlap(stn_list, gauge):
    gauge_select = gauge[gauge['event'].isin(stn_list)].sort_values(by='event')
    print('\nFlood Events Possibly Documented by Both Sources:\n')
    print(gauge_select['event'].unique())
    print(gauge_select['event_day'].unique())
    return gauge_select
    
# collect NHD dataset
def collect_nhd(layers):
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
        gdfs.append(gdf)
    return gdfs

# visualize flood event on map
def map_event(df):
    world = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER2022/STATE/tl_2022_us_state.zip")
    unique_events = df['event'].unique()
    colors = plt.cm.tab10(range(len(unique_events)))

    nhd_layers = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    nhd_gdfs = collect_nhd(nhd_layers)
    
    for state, data in df.groupby('state'):
        geometry = [Point(xy) for xy in zip(data['longitude'], data['latitude'])]
        gdf = gpd.GeoDataFrame(data, geometry=geometry)
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        state_boundary = world[world['STUSPS'] == state]
        state_boundary.boundary.plot(ax=ax, color='blue', linewidth=1.5)

        for nhd_gdf in nhd_gdfs:
            nhd_gdf.plot(ax=ax, color='gray', alpha=0.5)
        
        for idx, event in enumerate(unique_events):
            event_data = gdf[gdf['event'] == event]
            if not event_data.empty:
                category = event_data['category'].iloc[0]  
                marker = 'o' if category == 'gauge' else '^'
                event_data.plot(ax=ax, color=colors[idx], markersize=50, label=event, marker=marker)        
        ax.set_title(f'Events in {state}')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        west_lon, south_lat, east_lon, north_lat = state_boundary.total_bounds
        ax.set_xlim(west_lon, east_lon)
        ax.set_ylim(south_lat, north_lat)
        
        # Place legend outside the plot
        ax.legend(loc='upper left', title='Events', bbox_to_anchor=(1.02, 1), borderaxespad=0)
        
        plt.tight_layout()
        plt.savefig(f'figs/{state}_flood_event_map.png')

# TODO - Incomplete
def check_satellite(event_list_mod):
    id_images = {}

    for event in event_list_mod:
        event_dir = f'data/{event}/'
        if os.path.exists(event_dir):
            for filename in os.listdir(event_dir):
                parts = filename.split('_')
                id = parts[0]
                check_pattern = r'_(\d{8})T'
                match = re.findall(check_pattern, filename)
                if match:
                    date = match[0]
                if id not in id_images:
                    id_images[id] = {
                        'id': id,
                        'images': [],
                        'dates': [],
                        'dir': event
                    }
                id_images[id]['images'].append(filename)
                id_images[id]['dates'].append(date)
                id_images[id]['dir'].append(event)
    
    event_images_data = list(id_images.values())
    event_images_df = pd.DataFrame(event_images_data)
    print('Dataset Overview:\n', event_images_df.head())
    return event_images_df

# TODO 
def prep_satellite(df):

    # delete the event with 1 image 
    df_mod = df[df['date'].apply(len) > 1].copy()

    return df_mod

