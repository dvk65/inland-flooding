# Automated Assessment of Inland flooding from Satellite Observations

This project focus on developing an algorithm for automated assessment of inland flooding from satellite observations. Specifically, this algorithm collects satellite images corresponding to before-, during-, and after-flood events and applies the K-means clustering technique to identify flooded areas. The ultimate goal is to enhance flood detection capabilities, providing insights that can be applied to flood detection using drone measurements.

While the project initially targeted Maine, it has been expanded to include other states with similar flood characteristics. 

<img src="figs/workflow.png" width="800" alt="workflow">

| **Name** | **Source** | **Description** | **Format** | **Links** |
|---|---|---|---|---|
| [High-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) | [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/) | validated flood event observations from USGS | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [High-water levels](https://www.weather.gov/aprfc/terminology) | [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt) | real-time gauge water levels above moderate flood stage | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Sentinel-2 satellite images](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) | [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | satellite images corresponding to the areas of interest and timeframes defined by high-water marks and levels | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Cloud and Shadow](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) masks | [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) | cloud and shadow pixels to be dropped | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Normalized Difference Water Index](https://eos.com/make-an-analysis/ndwi/) masks | [Example](https://medium.com/@melqkiades/water-detection-using-ndwi-on-google-earth-engine-2919a9bf1951) | water body pixels defined by NDWI index to refine the algorithm's accuracy | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Flowlines](https://www.usgs.gov/ngp-standards-and-specifications/national-hydrography-dataset-nhd-data-dictionary-feature-classes) | [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) | Flowing water data used to enhance analysis and improve algorithm performance | Shapefile | 1.[Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |

## Instruction
- [Step 1: Collect flood event data](#step-1-collect-flood-event-data-high-water-marks-and-levels)
    - [High-water marks](#high-water-marks)
    - [High-water levels](#high-water-levels)
- [Step 2: Analyze the collected flood event data](#step-2-analyze-the-collected-flood-event-data)
- [Step 3: Collect Sentinel-2 true color imagery, cloud masks, and ndwi masks](#step-3-collect-sentinel-2-true-color-imagery-cloud-masks-and-ndwi-masks-corresponding-to-the-flood-event-data)
- [Step 4: Analyze and preprocess the Sentinel-2 true color imagery, cloud masks, and ndwi masks with NHD flowline added](#step-4-analyze-and-preprocess-sentinel-2-true-color-imagery-cloud-masks-and-ndwi-masks-with-nhd-flowline-added)
- [Step 5: Use KMeans clustering algorithm to assess inland flooding](#step-5-use-kmeans-clustering-technique-to-assess-inland-flooding)

### Step 1: Collect flood event data (high-water marks and levels)
Flood event data is derived from two primary sources: high-water marks available through the USGS STN Flood Event Data Portal and high-water levels extracted from real-time gauge data provided by USGS Water Data Services. 

#### High-water marks
[STN flood event database](https://stn.wim.usgs.gov/STNDataPortal/) is the primary source for observations documenting [high-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) during flood events. 

To collect and preprocess flood event data from the STN database, use the following command (estimated runtime: < 1 minute):
```
make stn
```

#### High-water levels
[USGS National Water Information System](https://waterdata.usgs.gov/nwis) is another source for flood event data by extracting real-time gauge water levels above the moderate flood stage. In this project,  when the water level of a gauge is above the moderate flood stage, it's considered as a flood event observation. 

To collect and preprocess gauge water levels above the [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding), use the following command (estimated runtime: 30-40 minutes):
```
make gauge
```

### Step 2: Analyze the collected flood event data
An analysis is conducted on the high-water marks/levels to:
- determine flood event dates from online flood event reports;
- visualize the distribution of flood events using countplots and maps;
- identify possible common flood events by comparing STN and gauge data.

To visualize the flood event observations, use the following command (estimated runtime: < 1 minute): 
```
make eda_flood_event
```

### Step 3: Collect Sentinel-2 true color imagery, cloud masks, and NDWI masks corresponding to the flood event data
Before collecting Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), we need to set up our own Google Cloud Platform project and authenticate using either our personal Google account or a service account. 

The sections `Create a Cloud project` and `Enable the Earth Engine API` in [Set up your Earth Engine enabled Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup) should be completed. A step-by-step demonstration can be found in [GUIDE.md](GUIDE.md#google-earth-engine-setup). 

To collect Sentinel 2 imagery from Google Earth Engine, use the following command (estimated runtime: 160 minutes): 
```
make s2
```

### Step 4: Analyze and preprocess Sentinel-2 true color imagery, cloud masks, and NDWI masks with NHD flowline added
Before applying the KMeans clustering algorithm, necessary preprocessing steps and an analysis are conducted on the Sentinel-2 images and masks to:
- extract the ideal dataset for KMeans clustering;
- prepare all masks for KMeans clustering.

Meanwhile, flowlines from National Hydrography Dataset are collected to enhance the analysis of flooded areas in Sentinel-2 images.

To run analysis and preparation on the images, use the following command (estimated runtime: 15-20 minutes):
```
make eda_s2
```

**Note**: 
- It's possible receiving the following UserWarning when runing `gpd.read_file()`but it won't affect the analysis in this project:
```
lib/python3.9/site-packages/pyogrio/raw.py:196: UserWarning: Measured (M) geometry types are not supported. Original type 'Measured 3D LineString' is converted to 'LineString Z'
  return ogr_read(
```

### Step 5: Use KMeans clustering technique to assess inland flooding
This section runs the KMeans clustering algorithm on the cleaned image dataset. 

To segment images, use the following command (estimated runtime: 30-40 minutes):
```
make kmeans
```

## Future Work
This section includes some potential improvements and other relevant resources that can be explored. 
### STN high-water marks
- `elev_ft` is one attribute that might be useful when combining with elevation model. However, it's important to remember that some high-water marks with the same location have different `elev_ft` values.
### Real-time gauge water levels
- [USGS National Water Information System Surface-Water Data](https://waterdata.usgs.gov/nwis/sw) includes various types of data. There might be a better approach to extract high-water levels which is more efficient and comphrehensive. 
- USGS has some other valuable flood-related platforms: One called [WaterWatch](https://waterwatch.usgs.gov/?id=ww_flood) and the other called [Flood Inundation Mapper](https://fim.wim.usgs.gov/fim/). Both resources utilizes the flow conditions of streamgages to evaluate flooded areas.
### Flowline
- The current approach includes lakes.
### Evaluation
- 

## Reference
