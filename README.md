# Flood Event Assessment and Visualization in New England Region

## Description
This project aims to assess and visualize flood events in the New England region. It utilizes the STN flood event database, gauge water level datasets, and the corresponding satellite imagery to provide insights into flood events and their impacts. 

## Instruction
### Step 1: Flood event data collection
The following command will collect and preprocess flood event data from STN database.
```
make stn_flood_event
```

The following command will collect and preprocess gauge water level above moderate flood stage.
```
make gauge_flood_event
```

### Step 2: EDA on flood event data
The following command will visualize the flood event.
```
make eda_flood_event
```
### Step 3: Sentinel 2 imagery collection
The following command will collect Sentinel 2 imagery from Google Earth Engine based on STN flood event data.
```
make stn_sentinel2
```
### Step 4: EDA on Sentinel 2 imagery
### Step 5: Imagery segmentation using KMeans Clustering

## Todo
- Finish the instruction part
- Export environment.yml
- Upload flood event analysis report
- Upload sentinel 2 analysis report
- Optimize KMeans clustering algorithm

## Reference
