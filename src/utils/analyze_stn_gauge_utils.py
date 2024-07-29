"""
This script includes the functions used to analyze STN and Gauge dataframes.

This file can be imported as a module and contains the following functions:
    * desc_data - print an overview of the specified dataset.
    * map_dates - returns the pandas Series representing the 'formed' and 'dissipated' dates for the event.
    * count_by_group - print the number of flood events group by a specified column.
    * plot_bar - visualize the dataset using a countplot.
    * convert_date - returns a pandas Series with the converted dates in the format 'YYYY-MM'.
    * check_overlap - returns a DataFrame representing the gauge data for events that overlap with the STN data.
    * collect_nhd - returns a list of GeoDataFrames, each representing an NHD layer.
    * map_event - creates a map for the flood events in each state
    * map_event_interactive - create an interactive map for flood events
"""
# import libraries
import folium
import requests
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from shapely.geometry import Point, shape

def desc_data(df):
    """
    Print an overview of the specified dataset
 
    Args:
        df (pd.DataFrame): The specified DataFrame
    """
    print('--------------------------------------------------------------')
    print(f'Dataset overview:')
    df.info()

    unique_count = df.nunique()
    print('\nnumber of unique values in each attribute:\n', unique_count)

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
        print('--------------------------------------------------------------')
        print('More precise data ranges for STN high-water mark data added\n')
        return pd.Series([formed, dissipated], index=['formed', 'dissipated'])

def count_by_group(df, var):
    """
    Print the number of flood events group by a specified column in descending order

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        var (str): The column name used to group data.
    """
    print('--------------------------------------------------------------')
    var_group = df.groupby(by=[var]).size().sort_values(ascending=False).to_frame(name='total_count')
    print(f'Table - Flood events group by {var}:\n', var_group)

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
    plt.figure(figsize=(14, 10))
    plt.title(f'{var} by state')
    plt.xlabel('State')
    plt.ylabel('Count')
    ax = sns.countplot(df, x='state', hue='event', order=order)
    
    for i in ax.containers:
        ax.bar_label(i)
    
    ax.legend(title='Event', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize='small')
    plt.tight_layout()

    plt.savefig(f'figs/stn_gauge/countplot_{filename}.png', bbox_inches='tight')
    plt.close()
    print('--------------------------------------------------------------')
    print(f'{filename} countplot created')

def convert_date(stn):
    """
    Convert the 'event' column to a standardized date format

    Args:
        stn (pd.DataFrame): The DataFrame with the 'event' column
    
    Returns:
        pd.Series: A pandas Series with the converted dates in the format 'YYYY-MM'
    """
    print('--------------------------------------------------------------')
    print('Date converted (e.g., 2018 March Extratropical Cyclone -> 2018-03)\n')
    date_stn = stn['event'].str.extract(r'(\d{4}) (\w+)')
    date_stn_mod = pd.to_datetime(date_stn.apply(lambda x: f"{x[0]} {x[1]}", axis=1), format='%Y %B', errors='coerce')
    date_stn_mod = date_stn_mod.dt.strftime('%Y-%m')
    print('Flood Event Date in STN (modified):\n', date_stn_mod.unique())
    return date_stn_mod

def check_overlap(stn_list, gauge):
    """
    Check for overlap between STN and gauge data

    Args:
        stn_list (list): A list of flood event names from the STN dataset
        gauge (pd.DataFrame): The DataFrame representing the gauge data
    
    Returns:
        pd.DataFrame: A DataFrame representing the gauge data for events that overlap with the STN data
    """
    print('--------------------------------------------------------------')
    gauge_select = gauge[gauge['event'].isin(stn_list)].sort_values(by='event').copy()
    print('Flood Events Possibly Documented by Both Sources:\n', gauge_select['event'].unique())
    print('\nexact day in gauge for further inspection:\n', gauge_select['event_day'].unique())
    return gauge_select
    
def collect_nhd(layers):
    """
    Collect and return NHD (National Hydrography Dataset) layers as GeoDataFrames

    Args:
        layers (list): A list of layer IDs to be collected from the NHD dataset
    
    Returns:
        list: A list of GeoDataFrames, each representing an NHD layer.  
    """
    print('NHD dataset added on map\n')
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

def map_event(df):
    """
    Visualize flood events on a map

    Args:
        df (pd.DataFrame): The DataFrame representing the flood event data
    
    Note:
        The plot is saved as a PNG file in the 'figs/stn_gauge' directory
    """
    print('--------------------------------------------------------------')
    print('Visualize flood events on map...\n')
    world = gpd.read_file("https://www2.census.gov/geo/tiger/TIGER2022/STATE/tl_2022_us_state.zip")
    unique_events = df[['event', 'category']].drop_duplicates()
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
        
        for idx, (event, category) in enumerate(unique_events.itertuples(index=False)):
            event_data = gdf[(gdf['event'] == event) & (gdf['category'] == category)]
            if not event_data.empty:
                marker = 'o' if category == 'gauge' else '^'
                event_data.plot(ax=ax, color=colors[idx], markersize=50, label=f'{event} ({category})', marker=marker)
        
        ax.set_title(f'Events in {state}')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        west_lon, south_lat, east_lon, north_lat = state_boundary.total_bounds
        ax.set_xlim(west_lon, east_lon)
        ax.set_ylim(south_lat, north_lat)
        
        ax.legend(loc='upper left', title='Events', bbox_to_anchor=(1.02, 1), borderaxespad=0)
        
        plt.tight_layout()
        plt.savefig(f'figs/stn_gauge/map_{state}.png')
        plt.close()

        print(f'complete - {state} flood event map created')

def map_event_interactive(df):
    """
    Create an interactive map for flood events using Folium

    Args:
        df (pd.DataFrame): The DataFrame representing the flood event data
    """
    print('--------------------------------------------------------------')
    print('Create an interactive map for flood events...\n')
    map_center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=8)
    marker_cluster = MarkerCluster().add_to(m)

    for i, row in df[df['category'] == 'gauge'].iterrows():
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

    for i, row in df[df['category'] != 'gauge'].iterrows():
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

    m.save('figs/stn_gauge/map_interactive.html')
