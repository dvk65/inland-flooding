# Automated Assessment of Inland flooding from Satellite Observations

This project focus on developing an algorithm for automated assessment of inland flooding from satellite observations. Specifically, this algorithm collects satellite images corresponding to before-, during-, and after-flood events and applies the K-means clustering technique to identify flooded areas. While the project initially targeted Maine, it has been expanded to include other states with similar flood characteristics. The ultimate goal is to enhance flood detection capabilities, providing insights that can be applied to flood detection using drone measurements.

The approach integrates the datasets described in the table below:
| **Name** | **Source** | **Description** | **Format** | **Links** |
|---|---|---|---|---|
| [High-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) | [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/) | validated flood event observations from USGS | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |
| [High-water levels](https://www.weather.gov/aprfc/terminology) | [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt) | real-time gauge water levels above moderate flood stage | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |
| [Sentinel-2 satellite images](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) | [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | satellite images corresponding to the areas of interest and timeframes defined by high-water marks and levels | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |
| [Cloud and Shadow](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) masks | [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) | cloud and shadow pixels to be dropped | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |
| [Normalized Difference Water Index](https://eos.com/make-an-analysis/ndwi/) masks | [Example](https://medium.com/@melqkiades/water-detection-using-ndwi-on-google-earth-engine-2919a9bf1951) | water body pixels defined by NDWI index to refine the algorithm's accuracy | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |
| [Flowlines](https://www.usgs.gov/ngp-standards-and-specifications/national-hydrography-dataset-nhd-data-dictionary-feature-classes) | [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) | Flowing water data used to enhance analysis and improve algorithm performance | Shapefile | 1.[Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>Data> |

## Instruction
- [Step 1: Collect flood event data](#step-1-collect-flood-event-data-high-water-marks-and-levels)
    - [High-water marks](#high-water-marks-from-usgs-stn-flood-event-data-portal)
    - [High-water levels](#high-water-levels-from-real-time-gauge-water-data)
- [Step 2: Analyze and preprocess the collected flood event data](#step-2-analyze-and-preprocess-the-collected-flood-event-data)
- [Step 3: Collect Sentinel-2 true color imagery, cloud masks, and ndwi masks](#step-3-collect-sentinel-2-true-color-imagery-cloud-masks-and-ndwi-masks-corresponding-to-the-flood-event-data)
- [Step 4: Analyze and preprocess the Sentinel-2 true color imagery, cloud masks, and ndwi masks](#step-4-analyze-and-preprocess-sentinel-2-true-color-imagery-cloud-masks-and-ndwi-masks)
- [Step 5: Download and explore the specified National Hydrography Dataset](#step-5-download-and-explore-the-specified-national-hydrography-dataset)
- [Step 6: Use KMeans clustering algorithm for image segmentation](#step-6-use-kmeans-clustering-technique-for-image-segmentation)

### Step 1: Collect flood event data (high-water marks and levels)
Flood event data is derived from two primary sources: high-water marks available through the USGS STN Flood Event Data Portal and high-water levels extracted from real-time gauge data provided by USGS Water Data Services. In this context, "flood events" refers to flood event categories, while "flood event observations" (high-water marks/levels) refers to individual data points.

#### High-water marks from USGS STN flood event data portal
[STN flood event database](https://stn.wim.usgs.gov/STNDataPortal/) is the primary source for observations documenting [high-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) during flood events. The original dataset includes 53 attributes. For this project, the selected attributes are `eventName`, `stateName`, `countyName`, `hwm_id`, `latitude`, `longitude`, and `hwm_locationdescription`. 

To collect and preprocess flood event data from the STN database, use the following command (estimated runtime: < 1 minute):
```
make stn
```

- This command includes the following steps:
    - download high-water marks from USGS STN Flood Event Data Portal in JSON format and convert it into a Pandas DataFrame;
    - execute necessary preprocessing steps and save the modified dataset as **df_stn_mod.csv**. 

#### High-water levels from real-time gauge water data
[USGS National Water Information System](https://waterdata.usgs.gov/nwis) is another source for flood event data by extracting real-time gauge water levels above the moderate flood stage. While the primary dataset for flood events is the STN flood event data, this dataset is included to collect additional Sentinel-2 imagery during flood events. Also, the flood event observations from this dataset provide a means to cross-reference the STN flood event data, providing a more comprehensive analysis. 

In this project,  when the water level of a gauge is above the moderate flood stage, it's considered as a flood event observation. To collect and preprocess gauge water levels above the [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding), use the following command (estimated runtime: 30-40 minutes):
```
make gauge
```

- This command includes the following steps:
    - collect real-time gauge water levels above the moderate flood stage;
    - execute necessary preprocessing steps and save the modified dataset as **df_gauge_mod.csv**.

### Step 2: Analyze and preprocess the collected flood event data
An analysis is conducted on the high-water marks/levels to:
- determine flood event dates from flood event reports;
- visualize the distribution of flood events using countplots and maps;
- identify common flood events by comparing STN and gauge data.

To visualize the flood event observations, use the following command (1): 
```
make eda_flood_event
```

The command will:
- print out summaries for both the STN high-water mark data and the gauge high-water level data;
- use `countplot` to show the number of observations in each unique flood events;
- create static maps to show the distribution of flood event observations. 

### Step 3: Collect Sentinel-2 true color imagery, cloud masks, and NDWI masks corresponding to the flood event data
Before collecting Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), we need to set up our own Google Cloud Platform project and authenticate using either our personal Google account or a service account. 

The sections `Create a Cloud project` and `Enable the Earth Engine API` in [Set up your Earth Engine enabled Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup) should be completed. A step-by-step demonstration can be found in [GUIDE.md](GUIDE.md#google-earth-engine-setup). 

To collect Sentinel 2 imagery from Google Earth Engine based on STN flood event data, use the following command (estimated runtime: 160 minutes): 
```
make s2
```

The command will:
- define the timeframes (`start_day` to `end_day`) used to collect images (`event_day` - 15 to `event_day` + 16)
    - *The value 16 is assigned because the `end_day` is exclusive when using [`filterDate`](https://developers.google.com/earth-engine/apidocs/ee-imagecollection-filterdate)*;
- remove invalid flood event observation that is too close to the already processed observations;
- remove invalid Sentinel-2 image in which cloud cover is greater than 20% or area is not fully captured;
- download three types of GeoTIFF files (Sentinel-2 true color image, NDWI mask using NDWI, and cloud mask) for each valid flood event observation

### Step 4: Analyze and preprocess Sentinel-2 true color imagery, cloud masks, and NDWI masks
Before applying the KMeans Clustering algorithm, we need to organize and analyze the collected satellite images.

To run analysis and preparation on the images, use the following command (estimated runtime: 15-20 minutes):
```
make eda_s2
```

- The original dataframe representing the image filename and its metedata has 379 image instances. The filtered dataframe has 102 image instances.
- The filtering steps includes:
    - dropping duplicate combinations of id and date (overlapping coverage of Sentinel-2 tiles)
    - dropping flood events without Sentinel-2 imagery during flood
    - selecting images from the ideal flood events
    - dropping Sentinel-2 images where more than 50% of the area is covered by clouds or shadows
    - dropping images token on the unwanted dates
- The detailed analysis can be found in [REPORT.md](REPORT.md#satellite-imagery-data-sentinel-2).


### Step 5: Download and explore the specified National Hydrography Dataset
This section collects National Hydrography Dataset for the DataFrame saved after Step 4. [The National Hydrography Dataset](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) is one part of the datasets that represent the surface water of the United States. This project utilizes the flowline shapefiles from NHD to enhance the analysis of flooding areas in Sentinel-2 images. 

The National Hydrography Dataset is downloaded from the [National Map Downloader](https://apps.nationalmap.gov/downloader/). This platform allows users to download the NHD as a shapefile by Hydrologic Unit, by state, or nationally. In this project, the NHD shapefile is downloaded by state. 

To download and plot the NHD, use the following command (estimated runtime: 7 minute):
```
make nhd
```

This commands will:
- download NHD datasets for CT, MA, and VT;
- plot the NHD flowlines on top of Sentinel-2 images during flood events for visual inspection.

**Note**: 
- A detailed description about the downloaded NHD datsets can be found in [GUIDE.md](GUIDE.md#dataset-documentation);
- An analysis of the plots can be found in [REPORT.md](REPORT.md#national-hydrography-dataset);
- Plotted figures can be found in [figs/s2_nhd](figs/s2_nhd);
- It's possible receiving the following UserWarning when runing `gpd.read_file()`but it won't affect the analysis in this project:
```
lib/python3.9/site-packages/pyogrio/raw.py:196: UserWarning: Measured (M) geometry types are not supported. Original type 'Measured 3D LineString' is converted to 'LineString Z'
  return ogr_read(
```

### Step 6: Use KMeans clustering technique for image segmentation
This section runs the KMeans clustering algorithm on the cleaned image dataset (30-40). 
```
make kmeans
```

This command will:
- add the image data, ndwi mask, and cloud/shadow mask (np.ndarray) to the existing DataFrame with image information;
- preprocess the image data (`StandardScaler`);
- run the default KMeans clustering algorithm;
- optimize KMeans clustering algorithm using `PCA` and other features;
- run the optimal KMeans clustering algorithm;
- evaluate the performance.

## Future Work
This section includes some potential improvements and other relevant resources that can be explored. 
### STN high-water marks
- `elev_ft` is one attribute that might be useful when combining with elevation model. However, it's important to remember that some high-water marks with the same location have different `elev_ft` values.
### Real-time gauge water levels
- [USGS National Water Information System Surface-Water Data](https://waterdata.usgs.gov/nwis/sw) includes various types of data. There might be a better approach to extract high-water levels which is more efficient and comphrehensive. 
- USGS has some other valuable flood-related platforms: One called [WaterWatch](https://waterwatch.usgs.gov/?id=ww_flood) and the other called [Flood Inundation Mapper](https://fim.wim.usgs.gov/fim/). Both resources utilizes the flow conditions of streamgages to evaluate flooded areas.
### Flowline
### Evaluation

## Reference
