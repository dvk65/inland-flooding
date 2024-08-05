"""
This script includes the functions used to analyze STN and Gauge dataframes.

This file can be imported as a module and contains the following functions:
    * run_eda - run an Exploratory Data Analysis (EDA) on the specified flood event data;
    * map_dates - returns the pandas Series representing the 'formed' and 'dissipated' dates for the event;
    * count_by_group - print the number of flood event observations group by a specified column;
    * plot_bar - visualize the dataset using a countplot;
    * collect_nhd - returns a list of GeoDataFrames, each representing an NHD layer;
    * map_event - creates a map for the flood event observations in each state;
    * map_event_interactive - create an interactive map for flood event observations.
"""
# import libraries
import folium
import requests
import pandas as pd
import numpy as np
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from shapely.geometry import Point, shape
from utils import global_utils

def run_eda(df, var, area_list):
    '''
    Run an Exploratory Data Analysis (EDA) on the specified flood event data

    Args:
        df (pd.DataFrame): The specified DataFrame to be analyzed
        var (str): The specified flood event data
        area_list (list of str): The specified area list
    '''
    print('***************************************************************************')
    print(f'ANALYZE {var.upper()} FLOOD EVENT OBSERVATIONS')
    title = f'{var} flood event observations'

    if var == 'stn' or var == 'gauge':
        global_utils.describe_df(df, var)
        # count by event
        count_by_group(df, 'event')

        # count by state
        count_by_group(df, 'state')

        # visualize by state
        plot_bar(df, title, var, area_list)
    elif var == 'stn and gauge':
        map_event(df, var)
        map_event_interactive(df)

def map_dates(event, date_range):
    """
    Add the formed and dissipated dates for the events
 
    Args:
        event (str): The event name for which the dates need to be mapped.
        date_range (dict): A dictionary representing the date ranges for each event.

    Returns:
        pd.Series: A pandas Series representing the 'formed' and 'dissipated' dates for the event.
    """
    if event in date_range:
        formed, dissipated = date_range[event]
        return pd.Series([formed, dissipated], index=['formed', 'dissipated'])

def count_by_group(df, var):
    """
    Print the count of flood events group by a specified column in descending order

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        var (str): The column name used to group data.
    """
    global_utils.print_func_header(f'count flood event observations group by {var}')
    var_group = df.groupby(by=[var]).size().sort_values(ascending=False).to_frame(name='total_count')
    print(var_group)

def plot_bar(df, var, filename, order):
    """
    Visualize the dataset using a countplot

    Args:
        df (pd.DataFrame): The DataFrame representing the data
        var (str): The variable to plot on the x-axis (e.g., 'state')
        filename (str): The name of the file to save the plot
        order (list): The order in which to display the x-axis categories

    Note:
        The plot is saved as a PNG file in the 'figs/stn_gauge' directory
    """
    global_utils.print_func_header(f'visualize {var} dataset using a countplot')
    plt.figure(figsize=(14, 10))
    plt.title(f'{var} by state')
    plt.xlabel('State')
    plt.ylabel('Count')
    ax = sns.countplot(df, x='state', hue='event', order=order)
    
    for i in ax.containers:
        ax.bar_label(i)
    
    ax.legend(title='Event', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize='small')
    plt.tight_layout()

    plt.savefig(f'figs/flood_event/countplot_{filename}.png', bbox_inches='tight')
    plt.close()

def collect_nhd(layers):
    """
    Collect and return NHD (National Hydrography Dataset) layers as GeoDataFrames

    Args:
        layers (list): A list of layer IDs to be collected from the NHD dataset
    
    Returns:
        list: A list of GeoDataFrames, each representing an NHD layer.  
    """
    print('complete - NHD layer created\n')
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

def map_event(df, var):
    """
    Visualize flood events on a map.

    Args:
        df (pd.DataFrame): The DataFrame representing the flood event data.
    
    Note:
        The plot is saved as a PNG file in the 'figs/flood_event' directory.
        Scale - smaller scale based on this approach (less detail)
    """
    global_utils.print_func_header(f'visualizing {var} on map using GeoPandas')
    world = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER2022/STATE/tl_2022_us_state.zip")
    unique_events = df['event'].drop_duplicates().reset_index(drop=True)
    num_unique_events = len(unique_events)

    # Generate a set of distinct colors
    palette = sns.color_palette("hsv", num_unique_events)  # Using seaborn's color palette for distinct colors
    colors = np.array(palette)

    # Map each unique event to a color
    event_color_mapping = {event: colors[idx] for idx, event in enumerate(unique_events)}

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
        
        for event in unique_events:
            event_data = gdf[gdf['event'] == event]
            if not event_data.empty:
                source = event_data['source'].iloc[0]
                marker = 'o' if source == 'gauge' else '^'
                event_data.plot(ax=ax, color=event_color_mapping[event], markersize=50, label=f'{event} ({source})', marker=marker)
        
        ax.set_title(f'Events in {state}')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        west_lon, south_lat, east_lon, north_lat = state_boundary.total_bounds
        ax.set_xlim(west_lon, east_lon)
        ax.set_ylim(south_lat, north_lat)
        
        ax.legend(loc='upper left', title='Events', bbox_to_anchor=(1.02, 1), borderaxespad=0)
        
        plt.tight_layout()
        plt.savefig(f'figs/flood_event/map_{state}.png')
        plt.close()

        print(f'complete - {state} flood event map created')

def map_event_interactive(df):
    """
    Create an interactive map for flood event observations using Folium

    Args:
        df (pd.DataFrame): The DataFrame representing the flood event data
    """
    global_utils.print_func_header('create an interactive map for flood event observations')
    map_center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=8)

    folium.TileLayer(
        tiles='https://basemap.nationalmap.gov/arcgis/rest/services/USGSHydroCached/MapServer/tile/{z}/{y}/{x}',
        attr='USGS National Map',
        name='USGS Hydro Cached',
        overlay=True,
        control=True
    ).add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df[df['source'] == 'gauge'].iterrows():
        popup_content = f"""
        <b>Event:</b> {row['event']}<br>
        <b>ID:</b> {row['id']}<br>
        <b>Location:</b> {row['latitude']}, {row['longitude']}<br>
        <b>Note:</b> {row['note']}<br>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='red')  
        ).add_to(m)

    for i, row in df[df['source'] != 'gauge'].iterrows():
        popup_content = f"""
        <b>Event:</b> {row['event']}<br>
        <b>ID:</b> {row['id']}<br>
        <b>Location:</b> {row['latitude']}, {row['longitude']}<br>
        <b>Note:</b> {row['note']}<br>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='blue')
        ).add_to(marker_cluster)

    m.save('figs/flood_event/map_interactive.html')
