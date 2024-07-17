# Flood Event Assessment and Visualization in New England Region

## Description
This project aims to assess and visualize flood events in the New England region. It utilizes the STN flood event database, gauge water level datasets, and the corresponding satellite imagery to provide insights into flood events and their impacts. 

## Instruction
### Step 1: Flood event data collection
In this project, [STN flood event database](https://stn.wim.usgs.gov/STNDataPortal/) is the primary source for flood events.To collect and preprocess flood event data from the STN database, use the following command. The estimated runtime is less than 1 minute. 
```
make stn_flood_event
```

Another approach to explore the flood events is by checking the water levels of gauges from [USGS National Water Information System](https://waterdata.usgs.gov/nwis).
To collect and preprocess gauge water levels above [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding%20is%20defined%20to%20have%20some,if%20moderate%20flooding%20is%20expected%20during%20the), use the following command. The estimated runtime is 30-40 minutes. 
```
make gauge_flood_event
```

The datasets are also available [here](https://drive.google.com/drive/folders/1m8dKBEbzPUuHp1urUjmGc0xb7KmVK_Ri?usp=sharing). 

### Step 2: EDA on flood event data
In this section, I implemented data visualization methods (countplot and map) to better understand the collected flood event data. To The following command will visualize the flood event. 
```
make eda_flood_event
```

### Step 3: Sentinel 2 imagery collection
Before collecting Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), we need to set up our own Google Cloud Platform project and authenticate using either our personal Google account or a service account. [Set up Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup) and [Python Installation](https://developers.google.com/earth-engine/guides/python_install) can be helpful. (A tutorial will be added later.)

The following command will collect Sentinel 2 imagery from Google Earth Engine based on STN flood event data. The estimated runtime is 80-90 minutes.

```
make stn_sentinel2
```

### Step 4: EDA on Sentinel 2 imagery
Before applying the KMeans Clustering algorithm, we need to analyze the collected satellite images.
### Step 5: Imagery segmentation using KMeans Clustering

## Todo
- Finish the instruction part
- Export environment.yml (yml incomplete)
- Improve flood event analysis report
- Upload sentinel 2 analysis report
- Optimize KMeans clustering algorithm

## Reference
