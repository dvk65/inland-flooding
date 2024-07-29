"""
This script includes the functions used to download Sentinel 2 imagery (True Color),
NDWI Index, and Cloud Mask.

This file can be imported as a module and contains the following functions:
    * map_color - returns a visualization of the image based on the specified visualization parameters.
    * check_region - returns if the percentage of valid pixels in the region meets or exceeds the threshold; otherwise, False.
    * cal_overlap - returns the percentage of overlap between two specified regions.
    * get_s2_sr_cld_col - returns the S2_SR_HARMONIZED collection where each image has a new 's2cloudless' property
    * add_cloud_bands - returns the image with two additional bands 'cld_pro' and 'is_cloud'.
    * add_shadow_bands - returns the image with three additional bands 'dark_pixels', 'cloud_transform', and 'shadows'.
    * add_cld_shdw_mask - returns a final mask that identifies the pixels affected by clouds or shadows
    * export_image_vis - download the image (True Color)
    * export_image_ndwi - download the ndwi for the image
    * export_image_cloud - download the cloud and shadow mask for the image
    * collect_sentinel2 - collect the imagery
    * collect_sentinel2_by_event - iterate over the event list to collect imagery
"""

# import libraries
import ee 
import os
import requests

# visualize an image with specific parameters
def map_color(image, select_vis):
  return image.visualize(**select_vis)

# check if the specified region in the image meets the coverage threshold based on valid (non-dark) pixels.
def check_region(image, region, threshold):

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

# calculate the percentage of overlap between two geographic regions
def cal_overlap(region1, region2):

    # calculate the area of the intersection of two regions
    intersect = region1.intersection(region2, ee.ErrorMargin(1))
    intersect_area = intersect.area().getInfo()

    # get the area of each region
    region1_area = region1.area().getInfo()
    region2_area = region2.area().getInfo()

    # calculate the percentage overlap
    overlap_per = (intersect_area / ((region1_area + region2_area) / 2)) * 100
    return overlap_per

# build a sentinel-2 collection
def get_s2_sr_cld_col(aoi, start_date, end_date):

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

# add the s2cloudless probability layer and derived cloud mask as bands to an S2 SR image input
def add_cloud_bands(img):
    # get s2cloudless image, subset the probability band
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # condition s2cloudless by the probability threshold value
    is_cloud = cld_prb.gt(40).rename('clouds')

    # add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))

# add dark pixels, cloud projection, and identified shadows as bands to an S2 SR image input
def add_shadow_bands(img):

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

# assemble all of the cloud and cloud shadow components and produce the final mask
def add_cld_shdw_mask(img):
    # add cloud component bands
    img_cloud = add_cloud_bands(img)
    # add cloud shadow component bands
    img_cloud_shadow = add_shadow_bands(img_cloud)
    # combine cloud and shadow mask, set cloud and shadow as value 1, else 0
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0).rename('cloudmask')
    # add the final cloud-shadow mask to the image
    return img_cloud_shadow.addBands(is_cld_shdw)

# export satellite image visualization
def export_image_vis(image, dir, scale, region, key):
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

# export ndwi
def export_image_ndwi(image, dir, scale, region, key):
    water_indices = image.select(['B3', 'B8'])
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

# export cloud and shadow mask
def export_image_cloud(image, dir, scale, region, key):

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

# collect sentinel 2 imagery
def collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, data, buffer_dis, overlap_threshold, pixel_threshold, scale):

    region_list = {}
    for index, row in data.iterrows():
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        region = ee.Geometry.Point(lon, lat).buffer(buffer_dis)
        event = row['event']
        key = row['id']

        overlap = any(cal_overlap(region, region_compare['region']) > overlap_threshold for region_compare in region_list.values() if region_compare['event'] == event)
        if overlap:
            print(f'{index}_{key} overlapping - skip')
        else:
            s2_sr_cld_col_eval = get_s2_sr_cld_col(region, row['start_day'], row['end_day'])
            dataset = s2_sr_cld_col_eval.map(add_cld_shdw_mask)

            select_vis = {
                'min': 0,
                'max': 3000,
                'bands': ['B4', 'B3', 'B2']
            }

            dataset_vis = dataset.map(lambda image: map_color(image, select_vis))
            for i in range(dataset_vis.size().getInfo()):
              image_vis = ee.Image(dataset_vis.toList(dataset_vis.size()).get(i))
              image = ee.Image(dataset.toList(dataset.size()).get(i))
              if check_region(image_vis, region, pixel_threshold).getInfo():
                export_image_vis(image_vis, dir_vis, scale, region, key)
                export_image_ndwi(image, dir_ndwi, scale, region, key)
                export_image_cloud(image, dir_cloud, scale, region, key)
            region_list[key] = {'region': region, 'event': event}   

# collect sentinel 2 imagery by event
def collect_sentinel2_by_event(df, buffer_dis, overlap_threshold, pixel_threshold, scale):
    event_list = df['event'].unique()
    for event in event_list:
        event_df = df[df['event'] == event].reset_index(drop=True)
        print(f'{event} has {len(event_df)} events.')
        dir_event = event.replace(' ', '_')
        dir_vis = f'data/img_sentinel2/{dir_event}/'
        dir_ndwi = f'data/img_sentinel2/{dir_event}_NDWI/'
        dir_cloud = f'data/img_sentinel2/{dir_event}_ClOUD/'
        os.makedirs(dir_vis, exist_ok=True)
        os.makedirs(dir_ndwi, exist_ok=True)
        os.makedirs(dir_cloud, exist_ok=True)
        collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, event_df, buffer_dis, overlap_threshold, pixel_threshold, scale)
        print(f"Finished processing for event: {event}")
