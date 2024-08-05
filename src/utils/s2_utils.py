"""
This script includes the functions used to download Sentinel 2 imagery (True Color),
NDWI Index, and Cloud Mask.

This file can be imported as a module and contains the following functions:
    * map_dates - returns a pandas Series representing the 'formed' and 'dissipated' dates for the flood event;
    * map_color - returns a visualization of the image based on the specified visualization parameters;
    * check_region - returns True if the percentage of valid pixels in the region meets or exceeds the threshold; otherwise, False;
    * cal_overlap - returns the percentage of overlap between two specified regions;
    * get_s2_sr_cld_col - returns the S2_SR_HARMONIZED collection where each image has a new 's2cloudless' property;
    * add_cloud_bands - returns the image with two additional bands 'cld_pro' and 'is_cloud';
    * add_shadow_bands - returns the image with three additional bands 'dark_pixels', 'cloud_transform', and 'shadows';
    * add_cld_shdw_mask - returns a final mask that identifies the pixels affected by clouds or shadows;
    * export_image_vis - download the image (True Color);
    * export_image_ndwi - download the water mask (ndwi) for the image;
    * export_image_cloud - download the cloud and shadow mask for the image;
    * collect_sentinel2 - collect the imagery for each event;
    * collect_sentinel2_by_event - iterate over the event list to collect imagery;
"""

# import libraries
import ee 
import os
import requests
import pandas as pd

def map_dates(event, date_range):
    """
    Add the formed and dissipated dates for the flood events
 
    Args:
        event (str): The event name for which the dates need to be mapped.
        date_range (dict): A dictionary representing the date ranges for each event.

    Returns:
        pd.Series: A pandas Series representing the 'formed' and 'dissipated' dates for the event.
    """
    if event in date_range:
        formed, dissipated = date_range[event]
        return pd.Series([formed, dissipated], index=['formed', 'dissipated'])

def map_color(image, select_vis):
    """
    Visualize an image with the specified parameters

    Args:
        image (ee.Image): The image to which the visualization parameters will be applied
        select_vis (dict): A dictionary including visualization parameters (e.g., {
                                'min': 0,
                                'max': 3000,
                                'bands': ['B4', 'B3', 'B2']
                            })

    Returns:
        ee.Image: The image with the visualization applied
    """
    return image.visualize(**select_vis)

def check_region(image, region, threshold):
    """
    Check if the specified region in the image meets the coverage threshold based on valid (non-dark) pixels

    Args:
        image (ee.Image): The imaged to be checked
        region (ee.Geometry): The region to check for valid pixel coverage
        threshold (float): The threshold for the region to be considered as valid

    Returns:
        ee.Boolean: A Boolean value representing if the coverage ratio meets the threshold

    Notes:
        This function is implemented because the satelliteimagery tiles may not fully cover the area 
    """
    # define the scale (resolution in meters)
    scale = 10

    # count the number of valid pixels in the region
    valid_pixel_count = image.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=region,
        scale=scale
    ).values().get(0)

    # calculate the total pixel count in the region
    pixel_value = ee.Number(scale**2)
    total_pixel_count = ee.Number(region.area()).divide(pixel_value)

    # calculate the coverage ratio
    coverage_ratio = ee.Number(valid_pixel_count).divide(total_pixel_count)

    # return the checked result
    return coverage_ratio.gte(threshold)

def cal_overlap(region1, region2):
    """
    Calculate the percentage of overlap between two geographic regions

    Args:
        region1 (ee.Geometry): The first region to be compared
        region2 (ee.Geometry): The second region to be compared

    Returns:
        float: The percentage of overlap between these two regions

    Notes:
        This function is applied to avoid collecting duplicate images resulting from the proximity of flood event observations
    """
    # calculate the area of the intersection of two regions
    intersect = region1.intersection(region2, ee.ErrorMargin(1))
    intersect_area = intersect.area().getInfo()

    # get the area of each region
    region1_area = region1.area().getInfo()
    region2_area = region2.area().getInfo()

    # calculate the percentage overlap
    overlap_per = (intersect_area / ((region1_area + region2_area) / 2)) * 100
    return overlap_per

def get_s2_sr_cld_col(aoi, start_date, end_date):
    """
    Build a Sentinel-2 collection with cloud probability information

    Args:
        aoi (ee.Geometry): The area of interest to filter the collection
        start_date (str): The start date of the date range for filtering the collection (included)
        end_date (str): The end date of the date range for filtering the collection (excluded)

    Returns:
        ee.ImageCollection : An ImageCollection including Sentinel-2 images with a new 's2cloudless' property
    """
    # import and filter S2_SR_HARMONIZED
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 20)))
    
    # import and filter s2cloudless
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))
    
    # join the filtered s2cloudless collection to the SR collection by the 'system:index' property
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))

def add_cloud_bands(img):
    """
    Add cloud probability and cloud mask bands to a Sentinel-2 image

    Args:
        img (ee.Image): The selected Sentinel-2 image
    
    Returns:
        ee.Image: The image with additional probability and clouds bands
    """
    # get s2cloudless image, subset the probability band
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # condition s2cloudless by the probability threshold value
    is_cloud = cld_prb.gt(40).rename('clouds')

    # add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))

def add_shadow_bands(img):
    """
    Identify potential cloud shadow pixels

    Args:
        img (ee.Image): The selected Sentinel-2 image

    Returns:
        ee.Image: The image with additional dark_pixels, cloud_transform, and shadows bands
    """
    # identify water pixels from the SCL band
    not_water = img.select('SCL').neq(6)

    # identify dark NIR pixels that are not water (potential cloud shadow pixels)
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(0.25*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # determine the direction to project cloud shadow from clouds (assumes UTM projection)
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # project shadows from clouds for the distance specified by the CLD_PRJ_DIST input
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, 3*10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))
    
    # identify the intersection of dark pixels with cloud shadow projection
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')

    # add dark pixels, cloud projection, and identified shadows as image bands
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

def add_cld_shdw_mask(img):
    """
    Assemble all of the cloud and cloud shadow components and produce the final mask

    Args:
        img (ee.Image): The selected image

    Returns:
        ee.Image:The final mask
    """
    # add cloud component bands
    img_cloud = add_cloud_bands(img)
    # add cloud shadow component bands
    img_cloud_shadow = add_shadow_bands(img_cloud)
    # combine cloud and shadow mask, set cloud and shadow as value 1, else 0
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0).rename('cloudmask')
    # add the final cloud-shadow mask to the image
    return img_cloud_shadow.addBands(is_cld_shdw)

def export_image_vis(image, dir, scale, region, key):
    """
    Download the satellite image with visualization

    Args:
        image (ee.Image): the selected image to be downloaded
        dir (str): the directory where the image is saved
        scale (int): The image resolution
        region (ee.Geometry): The region of interest
        key (str): The prefix in the filename
    """
    url = image.getDownloadUrl({
        'region': region,
        'scale': scale,
        'format': 'GEO_TIFF'
    })
    file_name = f'{key}_{image.id().getInfo()}_VIS'
    file_path = os.path.join(dir, f'{file_name}.tif')

    res = requests.get(url)
    with open(file_path, 'wb') as fd:
        fd.write(res.content)

def export_image_ndwi(image, dir, scale, region, key):
    """
    Download the water mask using the Normalized Difference Water Index

    Args:
        image (ee.Image): the selected image to be downloaded
        dir (str): the directory where the image is saved
        scale (int): The image resolution
        region (ee.Geometry): The region of interest
        key (str): The prefix in the filename
    """
    water_indices = image.select(['B3', 'B8'])

    # threshold can be adjusted
    water_mask = water_indices.normalizedDifference(['B3', 'B8']).gt(-0.25)

    url = water_mask.getDownloadUrl({
        'region': region,
        'scale': scale,
        'format': 'GEO_TIFF'
    })
    file_name = f'{key}_{image.id().getInfo()}_NDWI'
    file_path = os.path.join(dir, f'{file_name}.tif')

    res = requests.get(url)
    with open(file_path, 'wb') as fd:
        fd.write(res.content)

def export_image_cloud(image, dir, scale, region, key):
    """
    Download the cloud and shadow mask

    Args:
        image (ee.Image): the selected image to be downloaded
        dir (str): the directory where the image is saved
        scale (int): The image resolution
        region (ee.Geometry): The region of interest
        key (str): The prefix in the filename
    """
    image = image.select('cloudmask')
    url = image.getDownloadUrl({
        'region': region,
        'scale': scale,
        'format': 'GEO_TIFF'
    })
    file_name = f'{key}_{image.id().getInfo()}_CLOUD'
    file_path = os.path.join(dir, f'{file_name}.tif')

    res = requests.get(url)
    with open(file_path, 'wb') as fd:
        fd.write(res.content)

def collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, data, buffer_dis, overlap_threshold, pixel_threshold, scale):
    """
    Collect Sentinel-2 imagery for the specified flood event observations and region
    
    Args:
        dir_vis (str): The directory where the image (True Color) will be saved
        dir_ndwi (str): The directory where the water mask will be saved
        dir_cloud (str): The directory where the cloud and shadow mask will be saved
        data (pd.DataFrame): The DataFrame used to collect Sentinel-2 imagery
        buffer_dis (int): The distance to buffer around each location to define the region of interest
        overlap_threshold (int): The percentage threshold for region overlap
        pixel_threshold (float): The coverage ratio of valid pixels 
        scale (int): The resolution
    """
    region_list = {}
    for index, row in data.iterrows():
        
        # define the region of interest
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        region = ee.Geometry.Point(lon, lat).buffer(buffer_dis)
        event = row['event']
        key = row['id']

        # check the overlap between regions
        overlap = any(cal_overlap(region, region_compare['region']) > overlap_threshold for region_compare in region_list.values() if region_compare['event'] == event)
        if overlap:
            print(f'{index}_{key} overlapping - skip')
        else:
            
            # obtain the Sentinel-2 collection with cloud and shadow mask
            s2_sr_cld_col_eval = get_s2_sr_cld_col(region, row['start_day'], row['end_day'])
            dataset = s2_sr_cld_col_eval.map(add_cld_shdw_mask)

            # define and apply visualization parameters
            select_vis = {
                'min': 0,
                'max': 3000,
                'bands': ['B4', 'B3', 'B2']
            }
            dataset_vis = dataset.map(lambda image: map_color(image, select_vis))

            for i in range(dataset_vis.size().getInfo()):
              image_vis = ee.Image(dataset_vis.toList(dataset_vis.size()).get(i))
              image = ee.Image(dataset.toList(dataset.size()).get(i))

              # check valid pixels
              if check_region(image_vis, region, pixel_threshold).getInfo():
                
                # download images
                export_image_vis(image_vis, dir_vis, scale, region, key)
                export_image_ndwi(image, dir_ndwi, scale, region, key)
                export_image_cloud(image, dir_cloud, scale, region, key)
            region_list[key] = {'region': region, 'event': event}   

def collect_sentinel2_by_event(df, buffer_dis, overlap_threshold, pixel_threshold, scale):
    """
    Collect Sentinel-2 imagery by unique event ids

    Args:
        df (pd.DataFrame): The DataFrame used to collect images
        buffer_dis (int): The distance to buffer around each location to define the region of interest
        overlap_threshold (int): The percentage threshold for region overlap
        pixel_threshold (float): The coverage ratio of valid pixels 
        scale (int): The resolution
    """

    # get the list of unique flood events
    event_list = df['event'].unique()
    for event in event_list:
        event_df = df[df['event'] == event].reset_index(drop=True)
        print(f'{event} has {len(event_df)} events.')

        # create the directory
        dir_event = event.replace(' ', '_')
        dir_vis = f'data/img_s2/{dir_event}/'
        dir_ndwi = f'data/img_s2/{dir_event}_NDWI/'
        dir_cloud = f'data/img_s2/{dir_event}_CLOUD/'
        os.makedirs(dir_vis, exist_ok=True)
        os.makedirs(dir_ndwi, exist_ok=True)
        os.makedirs(dir_cloud, exist_ok=True)

        # collect and download Sentinel-2 imagery for the current event
        collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, event_df, buffer_dis, overlap_threshold, pixel_threshold, scale)
        print(f"Finished processing for event: {event}")
