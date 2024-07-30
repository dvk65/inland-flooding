# Flood Event Assessment and Visualization in New England Region

## Description
This project aims to assess and visualize flood events in the New England region (CT, ME, MA, NH, RI, VT). It primarily utilizes the STN flood event data (high water marks), gauge real-time water level data (high water levels), and the corresponding satellite imagery to provide insights into flood events and their impacts. 

## Table of Contents
- [Step 1: Flood event data collection](#step-1-flood-event-data-collection)
- [Step 2: Analysis of flood event data](#step-2-analysis-of-flood-event-data)
- [Step 3: Sentinel 2 imagery collection](#step-3-sentinel-2-imagery-collection)
- [Step 4: Analysis of Sentinel-2 imagery](#step-4-analysis-of-sentinel-2-imagery)
- [Step 5: Image segmentation of Sentinel-2 imagery using KMeans Clustering](#step-5-image-segmentation-using-kmeans-clustering)
- [Step 6: Evaluation](#step-6-evaluation)

## Instruction
### Step 1: Flood event data collection
[STN flood event database](https://stn.wim.usgs.gov/STNDataPortal/) is the primary source for flood event observations that documents [high-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) during flood events. The original dataset includes 53 attributes. For this project, the selected attributes are `eventName`, `stateName`, `countyName`, `hwm_id`, `latitude`, `longitude`, and `hwm_locationdescription`. 
To collect and preprocess flood event data from the STN database, use the following command (estimated runtime: < 1 minute):
```
make collect_stn
```

The real-time water levels of gauges from [USGS National Water Information System](https://waterdata.usgs.gov/nwis) is another source for flood events. In this project,  when the water level of a gauge is above the moderate flood stage, it's considered as a flood event. To increase the number of flood event instances, high water levels are also collected. 
To collect and preprocess gauge water levels above the [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding), use the following command (estimated runtime: 30-40 minutes):
```
make collect_gauge
```

The datasets are available [here](https://drive.google.com/drive/folders/1m8dKBEbzPUuHp1urUjmGc0xb7KmVK_Ri?usp=sharing). 

### Step 2: Analysis of flood event data
After collecting STN high water mark data and gauge high water level data, an analysis is conducted to:
- obtain the flood event dates based on flood event reports;
- examine the distribution of flood events based on charts and maps;
- identify the common flood events based on the overlap between STN and gauge data.

The following command will visualize the flood event. 
```
make analyze_stn_gauge
```

### Step 3: Sentinel 2 imagery collection
Before collecting Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), we need to set up our own Google Cloud Platform project and authenticate using either our personal Google account or a service account. 

The sections `Create a Cloud project` and `Enable the Earth Engine API` in [Set up your Earth Engine enabled Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup) should be completed. (A tutorial will be added later.)

To collect Sentinel 2 imagery from Google Earth Engine based on STN flood event data, use the following command (estimated runtime: 120 minutes): 
```
make collect_sentinel2
```

The example dataset is available [here](https://drive.google.com/drive/folders/1m8dKBEbzPUuHp1urUjmGc0xb7KmVK_Ri?usp=sharing).

### Step 4: Analysis of Sentinel 2 imagery
Before applying the KMeans Clustering algorithm, we need to analyze the collected satellite images.

```
make analyze_image
```

### Step 5: Image segmentation using KMeans Clustering

```
make run_kmeans
```

### Step 6: Evaluation
```
make run_eval
```

## Todo
- Finish the instruction part
- Improve Report.md (flood event/image/kmeans analysis)
- Optimize KMeans clustering algorithm
- Add the evaluation part

## Reference
