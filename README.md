# Automated Assessment of Inland flooding from Satellite Observations

This project focus on developing an algorithm for automated assessment of inland flooding from satellite observations. Specifically, this algorithm collects satellite images corresponding to before-, during-, and after-flood events and applies the K-means clustering technique to identify flooded areas. The ultimate goal is to enhance flood detection capabilities, providing insights that can be applied to flood detection using drone measurements.

While the project initially targeted Maine, it has been expanded to include other states with similar flood characteristics. 

<img src="figs/workflow.png" width="800" alt="workflow">

The approach integrates the datasets described in the table below:
| **Name** | **Source** | **Description** | **Format** | **Links** |
|---|---|---|---|---|
| [High-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) | [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/) | validated flood event observations from USGS | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |
| [High-water levels](https://www.weather.gov/aprfc/terminology) | [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt) | real-time gauge water levels above moderate flood stage | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |
| [Sentinel-2 images](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) | [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | satellite images corresponding to the areas of interests and timeframes defined by high-water marks and levels | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |
| [Cloud and Shadow](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) masks | [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) | cloud and shadow pixels to be removed | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |
| [NDWI](https://eos.com/make-an-analysis/ndwi/) masks | [NDWI tutorial](https://medium.com/@melqkiades/water-detection-using-ndwi-on-google-earth-engine-2919a9bf1951) | water body pixels defined by Normalized Difference Water Index | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |
| [Flowlines](https://www.usgs.gov/ngp-standards-and-specifications/national-hydrography-dataset-nhd-data-dictionary-feature-classes) masks | [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) | routes that make up a linear surface water drainage network | Shapefile | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) |

_Note: The [data](https://drive.google.com/drive/folders/1iFKHeHfNnRrpxUlsN3PIxYGxEh9IeB3n?usp=sharing) folder structure and contents are explained in [GUIDE](GUIDE.md)._

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

Before collecting Sentinel-2 imagery with this approach, remember to replace the project ID in the Cloud project in `s2.py` (`ee.Initialize(project='demoflood0803')`) with your project ID. To collect Sentinel-2 imagery from Google Earth Engine, use the following command (estimated runtime: 160 minutes): 
```
make s2
```

### Step 4: Analyze and preprocess Sentinel-2 true color imagery, cloud masks, and NDWI masks with NHD flowline added
Before applying the KMeans clustering algorithm, necessary preprocessing steps and an analysis are conducted on the Sentinel-2 images and masks to:
- extract the ideal dataset for KMeans clustering;
- prepare all masks for KMeans clustering.

Meanwhile, flowlines from National Hydrography Dataset are collected to enhance the analysis of flooded areas in Sentinel-2 images and improve the K-means clustering algorithm.

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

## Reference
### Data
- [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/)
- [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt)
- [National Water Prediction Service](https://water.noaa.gov/#@=-96.401081,38.1465724,3.3479233&b=topographic&g=obsFcst,1!1!1!1!1!1!1!1!1!1!1!1!1!1!1!0!0!0!0!0,0.5,1!1!1!1!0,0,0&ab=0,0,#D94B4A,1,1,1,#cccccc,1,0,0,#B243B1,1,0,0,#98E09A,1&a=hydrologic,0.35&s=0,0,0.9,0.9&n=false,#72afe9,0.9,0,0.9,0,0.9&p=false,0.75,0,7,0,1,2024,8,15,0&d=0,0,1,1,1,1,1,1,#006EFF,1,#006EFF,1,#006EFF&q=)
- [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/national-hydrography-dataset)

### Paper
- [A multi-sensor approach for increased measurements of floods and their societal impacts from space](https://www.nature.com/articles/s43247-023-01129-1)
- [Remote sensing for flood inundation mapping using various processing methods with Sentinel-1 and Sentinel-2](https://isprs-archives.copernicus.org/articles/XLVIII-M-1-2023/339/2023/isprs-archives-XLVIII-M-1-2023-339-2023.pdf)