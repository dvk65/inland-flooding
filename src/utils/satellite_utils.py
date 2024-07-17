import ee 
import time
import os
import requests

def map_color(image, select_vis):
  return image.visualize(**select_vis)

# calculate the percentage of the region that is covered by valid (non-dark) pixels
def check_region(image, region, threshold, folder):
  if folder == 'landsat8':
    scale = 30
  else:
    scale = 10
  valid_pixel_count = image.reduceRegion(
      reducer=ee.Reducer.count(),
      geometry=region,
      scale=scale
  ).values().get(0)

  pixel_value = ee.Number(scale**2)
  total_pixel_count = ee.Number(region.area()).divide(pixel_value)
  coverage_ratio = ee.Number(valid_pixel_count).divide(total_pixel_count)

  return coverage_ratio.gte(threshold)

# calculate the intersection
def cal_overlap(region1, region2):
  intersect = region1.intersection(region2, ee.ErrorMargin(1))
  intersect_area = intersect.area().getInfo()
  region1_area = region1.area().getInfo()
  region2_area = region2.area().getInfo()
  overlap_per = (intersect_area / ((region1_area + region2_area) / 2)) * 100
  return overlap_per

# build a sentinel-2 collection
def get_s2_sr_cld_col(aoi, start_date, end_date):
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 20)))
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))
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
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')
    is_cloud = cld_prb.gt(40).rename('clouds')
    return img.addBands(ee.Image([cld_prb, is_cloud]))

# add dark pixels, cloud projection, and identified shadows as bands to an S2 SR image input
def add_shadow_bands(img):
    not_water = img.select('SCL').neq(6)
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(0.25*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, 3*10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

# assemble all of the cloud and cloud shadow components and produce the final mask
def add_cld_shdw_mask(img):
    img_cloud = add_cloud_bands(img)
    img_cloud_shadow = add_shadow_bands(img_cloud)
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0).rename('cloudmask')
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
def export_image_ndwi(image, dir, scale, region, key, satellite):
    if satellite == 'sentinel2':
        water_indices = image.select(['B3', 'B8'])
        water_mask = water_indices.normalizedDifference(['B3', 'B8']).gt(-0.25)
    elif satellite == 'landsat8':
        water_indices = image.select(['SR_B5', 'SR_B4'])
        water_mask = water_indices.normalizedDifference(['SR_B5', 'SR_B4']).gt(-0.25)

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
def export_image_cloud(image, dir, scale, region, key, satellite):
  if satellite == 'sentinel2':
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
def collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, data, buffer_dis, overlap_threshold, pixel_threshold, satellite, scale):
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
              if check_region(image_vis, region, pixel_threshold, satellite).getInfo():
                export_image_vis(image_vis, dir_vis, scale, region, key)
                export_image_ndwi(image, dir_ndwi, scale, region, key, satellite)
                export_image_cloud(image, dir_cloud, scale, region, key, satellite)
            region_list[key] = {'region': region, 'event': event}

def collect_sentinel2_by_event(df, wait_time, buffer_dis, overlap_threshold, pixel_threshold, satellite, scale, date_range):
    event_list = df['event'].unique()
    for event in event_list:
       event_df = df[df['event'] == event].reset_index(drop=True)
       event_df['start_day'] = date_range[event][0]
       event_df['end_day'] = date_range[event][1]
       print(f'{event} has {len(event_df)} events.')
       dir_event = event.replace(' ', '_')
       dir_vis = f'data/{dir_event}/'
       dir_ndwi = f'data/{dir_event}_NDWI/'
       dir_cloud = f'data/{dir_event}_ClOUD/'
       os.makedirs(dir_vis, exist_ok=True)
       os.makedirs(dir_ndwi, exist_ok=True)
       os.makedirs(dir_cloud, exist_ok=True)
       collect_sentinel2(dir_vis, dir_ndwi, dir_cloud, event_df, buffer_dis, overlap_threshold, pixel_threshold, satellite, scale)
    #    time.sleep(wait_time)
       print(f"Finished processing for event: {event}")


