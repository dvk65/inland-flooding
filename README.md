# Flood Event Assessment and Visualization in New England Region

This project aims to assess and visualize flood events in the New England region (CT, ME, MA, NH, RI, VT). It primarily utilizes the STN flood event data (high water marks), gauge real-time water level data (filtered high water levels), and the corresponding satellite imagery to provide insights into flood events and their impacts. 

## Table of Contents
- [Step 1: Collect flood event data](#step-1-collect-flood-event-data)
- [Step 2: Analyze and prepare the collected flood event data](#step-2-analyze-and-prepare-the-collected-flood-event-data)
- [Step 3: Collect Sentinel 2 imagery associated with the flood event data](#step-3-collect-sentinel-2-imagery-associated-with-the-flood-event-data)
- [Step 4: Analyze and prepare the Sentinel-2 imagery](#step-4-analyze-and-prepare-sentinel-2-imagery)
- [Step 5: Download and plot the specified National Hydrography Dataset (DONE)](#step-5-download-and-plot-the-specified-national-hydrography-dataset)
- [Step 6: Use KMeans clustering algorithm to segment Sentinel-2 imagery](#step-6-use-kmeans-clustering-algorithm-to-segment-sentinel-2-imagery)
- [Step 7: Evaluate the performance](#step-7-evaluate-the-performance)

## Instruction
### Step 1: Collect flood event data
[STN flood event database](https://stn.wim.usgs.gov/STNDataPortal/) is the primary source for observations documenting [high-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) during flood events. The original dataset includes 53 attributes. For this project, the selected attributes are `eventName`, `stateName`, `countyName`, `hwm_id`, `latitude`, `longitude`, and `hwm_locationdescription`. 

To collect and preprocess flood event data from the STN database, use the following command (estimated runtime: < 1 minute):
```
make stn
```

- The goal is to integrate flood event data with Sentinel-2 imagery to analyze flood extents. Therefore, it is crucial to avoid duplicate Sentinel-2 images and exclude any observations before 2015, as Sentinel-2 imagery is available from 2015. 
- The orginal STN flood event dataset has 3502 observations with 53 attributes. The The modified dataset has 889 observations with 7 attributes (`id`, `event`, `state`, `county`, `latitude`, `longitude`, and `note`). 
- The unique flood events included are `2018 January Extratropical Cyclone`, `2018 March Extratropical Cyclone`, `2021 Henri`, `2023 July MA NY VT Flood`, and `2023 December East Coast Cyclone`. 
- Since the earliest flood event in the modified dataset occurred in 2018, Sentinel-2 Level-2A imagery (available from 2017-03-28) is used without worrying about missing valuable flood event data. This date is also used when collecting real-time water level data from gauges. 
    - In [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), there're two Sentinel-2 datasets including Level-1C dataset and Level-2A dataset. Both provide high-resolution (10m) imagery, but Level-2A includes atmospheric correction, offering more accurate surface reflectance data. 

The real-time water levels of gauges from [USGS National Water Information System](https://waterdata.usgs.gov/nwis) provide an additional source for flood events. While the primary dataset for flood events is the STN flood event data, this dataset is included to collect additional Sentinel-2 imagery during flood events. Also, the flood event observations from this dataset provide a means to cross-reference the STN flood event data, providing a more comprehensive analysis. 

In this project,  when the water level of a gauge is above the moderate flood stage, it's considered as a flood event observation. To collect and preprocess gauge water levels above the [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding), use the following command (estimated runtime: 30-40 minutes):
```
make gauge
```

- Collecting gauge water levels above the moderate flood stage includes three steps:
    - collect NWSLI identifiers and descriptions for the gauges from NOAA.
    - identify the corresponding usgsid for each gauge and gather flood-related information, including flood stage thresholds and flood impacts.
    - collect real-time water levels using usgsid and compare them against the flood stage thresholds to identify observations where levels exceed the moderate flood stage.
- The date range for collecting water level is from 2017-03-28 (start of Sentinel-2 Level-2A imagery availability) to 2024-05-23 (initial data collection date)
- For clarity, the dataset detailing gauge water levels above the moderate flood stage is referred to as the "high-water level" dataset.
- The high-water level dataset includes 218 observations and 9 attributes.

The ready-to-use datasets are available [here](https://drive.google.com/drive/folders/1QHi26bRnB58R46VIkkpXLiby3xe0nm_W?usp=sharing). 

### Step 2: Analyze and prepare the collected flood event data
After collecting STN high-water mark data and gauge high-water level data, an analysis is conducted to:
- determine flood event dates from flood event reports;
- visualize the distribution of flood events using barplots and maps;
- identify common flood events by comparing STN and gauge data.

To visualize the flood event observations, use the following command: 
```
make eda_flood_event
```

The command will:
- print out summaries for both the STN high-water mark data and the gauge high-water level data;
- use `countplot` to show the number of observations in each unique flood events;
- create both static and interactive maps to show the distribution of flood event observations. 
- The detailed analysis can be found in [REPORT.md](REPORT.md).

### Step 3: Collect Sentinel 2 imagery associated with the flood event data
Before collecting Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), we need to set up our own Google Cloud Platform project and authenticate using either our personal Google account or a service account. 

The sections `Create a Cloud project` and `Enable the Earth Engine API` in [Set up your Earth Engine enabled Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup) should be completed. A step-by-step demonstration can be found in [GUIDE.md](GUIDE.md). 

To collect Sentinel 2 imagery from Google Earth Engine based on STN flood event data, use the following command (estimated runtime: 180 minutes): 
```
make s2
```

- This command downloads three types of .tiff images including the satellite image (True Color), the water mask using NDWI, and the cloud/shadow mask using [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless).
- To ensure that we can collect high-quality images before/during/after images, the `start_day` and `end_day` used to collect images is between event start day - 25 and event end day + 25. 

The ready-to-use dataset is available [here](https://drive.google.com/drive/folders/1QHi26bRnB58R46VIkkpXLiby3xe0nm_W?usp=sharing).


### Step 4: Analyze and prepare Sentinel-2 imagery
Before applying the KMeans Clustering algorithm, we need to organize and analyze the collected satellite images.

To run analysis and preparation on the images, use the following command (estimated runtime:  minute):
```
make eda_s2
```

- The original dataframe representing the image filename and its metedata has 541 image instances. The filtered dataframe has 104 image instances.
- The filtering steps includes:
    - dropping duplicate combinations of id and date (overlapping coverage of Sentinel-2 tiles)
    - dropping flood events without Sentinel-2 imagery during flood
    - selecting images from the ideal flood events
    - dropping Sentinel-2 images where more than 50% of the area is covered by clouds or shadows
    - dropping images token on the unwanted dates
- The detailed analysis can be found in [REPORT.md](REPORT.md).


### Step 5: Download and plot the specified National Hydrography Dataset
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
- An analysis of the plots can be found in [REPORT.md](REPORT.md);
- Plotted figures can be found in [figs/s2_nhd](figs/s2_nhd);
- It's possible receiving the following UserWarning when runing `gpd.read_file()`but it won't affect the analysis in this project:
```
lib/python3.9/site-packages/pyogrio/raw.py:196: UserWarning: Measured (M) geometry types are not supported. Original type 'Measured 3D LineString' is converted to 'LineString Z'
  return ogr_read(
```

### Step 6: Use KMeans clustering algorithm to segment Sentinel-2 imagery (Ongoing)
This section runs the KMeans clustering algorithm on the cleaned image dataset. 
```
make kmeans
```

### Step 7: Evaluate the performance (Onging)
```
make evaluation
```

### Testing (used for testing functions)
```
make test
```

## Todo
- Finish the instruction part (almost)
- Improve Report.md (flood event/image/kmeans analysis) (almost)
- Optimize KMeans clustering algorithm and classification part
- Add the evaluation part

## Reference
