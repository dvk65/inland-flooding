# Automated Assessment of Inland flooding from Satellite Observations

This project focuses on developing an algorithm for automated assessment of inland flooding from satellite observations. Specifically, this algorithm collects satellite images corresponding to before-, during-, and after-flood events and applies the K-means clustering technique to identify flooded areas. The ultimate goal is to enhance flood detection capabilities, providing insights that can be applied to flood detection using drone measurements.

While the project initially targeted some states in New England Region, it has been expanded to include Maine. The current code base only includes the collection of Maine and Vermont data.

## Primary Deliverables
- [README.md](README.md) - An overview of the project, including step-by-step [instructions](README.md#instruction) to replicate the results;
- [REPORT.md](REPORT.md) - A detailed report on the project's objectives, methodology, and results;
- [GUIDE.md](GUIDE.md) - A guide to help users set up the required environment and explore relevant details about the datasets in this project. 

## Workflow and Datasets
Below is the workflow for the project:

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

To collect and preprocess gauge water levels above the [moderate flood stage](https://www.weather.gov/aprfc/terminology#:~:text=Moderate%20Flooding), use the following command (estimated runtime: 15 - 20 minutes):
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
To collect Sentinel 2 imagery from [Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2), you need to satisfy the following requirements, as listed in the [Google Earth Engine Tutorial](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup):
- Ensure you have a **Google Account**;
- Create or select an existing **Google Cloud Project**;
- Enable the **Earth Engine API** within your Google Cloud Project. 

To set up your Earth Engine-enabled Cloud Project, follow the steps in the [Google Earth Engine setup guide](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup). Ensure you complete the `Create a Cloud Project` and `Enable the Earth Engine API` sections. A step-by-step walkthrough can be found in [GUIDE.md](GUIDE.md#google-earth-engine-setup).

Before collecting Sentinel-2 imagery, make sure to update the project ID in `s2.py` by replacing `demoflood0803` with your own project ID (`ee.Initialize(project='your_project_id')`). Then, to start the collection process, run the following command (estimated runtime: 155 minutes):
```
make s2
```

### Step 4: Analyze and preprocess Sentinel-2 true color imagery, cloud masks, and NDWI masks with NHD flowline added
Before applying the KMeans clustering algorithm, necessary preprocessing steps and an analysis are conducted on the Sentinel-2 images and masks to:
- extract the ideal dataset for KMeans clustering;
- prepare all masks for KMeans clustering.

Meanwhile, flowlines from National Hydrography Dataset are collected to enhance the analysis of flooded areas in Sentinel-2 images and improve the K-means clustering algorithm.

To run analysis and preparation on the images, use the following command (estimated runtime: 5 - 6 minutes):
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

To segment images, use the following command (estimated runtime: 20 - 22 minutes):
```
make kmeans
```

## Extensions as mentioned in proposal:

### 1. Exploring the MEAN and MERN Stack while Looking at Integration Options (Feb 21)
- Explored full-stack web development frameworks: MEAN (MongoDB, Express, Angular, Node.js) and MERN (MongoDB, Express, React, Node.js)
- Evaluated integration needs for geospatial data and large satellite imagery
- Found both stacks to be too heavy and unsuitable for rendering and interacting with large raster datasets
- Identified performance issues when attempting to process and visualize high-resolution satellite data in-browser with MERN/MEAN
- Chose to pivot away from traditional web app development
- Selected Observable as a lightweight, open-source, interactive notebook-based alternative for geospatial visualization

### 2. Visualization and Overlay (March 7)
- Used Observable notebooks to create interactive, browser-friendly visualizations of shapefiles and NDWI data
- Integrated and overlaid flood boundaries and river flowlines for Maine and Vermont
- Incorporated raster and vector data layers to better understand flood patterns
- Began focusing on Maine data to assess challenges of low-visibility and cluttered imagery
- Noted that Observable provided better rendering and faster prototyping than traditional web stacks
- Designed exploratory maps that allow users to toggle between overlays like NDWI, flood boundaries, and flowlines

 ### 3. Flood Events Visualization (March 21)
- Processed limited "during flood" satellite imagery from Maine.
- Identified cluttered and fragmented flood visuals in areas around flowlines, especially under snowy or cloudy conditions.
- Enhanced visualization by color-coding river flowlines in hot pink to improve distinguishability from flooded zones.
- Developed an unsupervised clustering method (KMeans) for pixel classification using RGB values.
- Introduced "distance to flowline" as a fourth feature alongside RGB, improving spatial awareness in clustering.
- Found that this addition slightly improved the model’s focus near rivers, though overall accuracy remained a challenge due to noisy data.

 ### 4. Deploying the Web Application (April 11)
- Initially planned to deploy a standalone web app using full-stack tools.
- Pivoted due to the volume of data and performance limitations in browser-based environments.
- Focused instead on a modular Observable-based visualization environment for accessibility and open-source sharing.
- Avoided complex backend hosting and authentication, as Observable allowed for public, lightweight visualizations.
- [Explored ways of handling big data when deploying a web application](https://docs.google.com/document/d/1zeiTgkxdsBEhnq9DyQo881WCS3tXlJ3tPtyCI1jGaDs/edit?usp=sharing)

 ### 5. Final Submission
- Compiled all processed Maine and Vermont datasets, including shapefiles, satellite imagery, and model outputs.
- Maine presented a unique set of difficulties that heavily impacted both the quality and quantity of usable flood-related imagery:
    - Sparse Flood Events with Satellite Overlap:
        Unlike Vermont, which had an abundance of satellite images captured during flood events, Maine had very few usable images where flood incidents coincided with satellite passes. This significantly limited the training and validation opportunities for our unsupervised model.
    - Cluttered and Inconsistent Flowlines:
        We relied on flowline shapefiles from the National Hydrography Dataset (NHD) to understand the water body's underlying structure. In Maine, these flowlines were often disjointed, cluttered, or fragmented, making it difficult to define a continuous river path. This lack of continuity created noise and confusion when trying to correlate flooded regions with natural water pathways.
    - Noisy Imagery Due to Weather Conditions:
        Snow-covered regions and cloudy imagery added visual clutter and reduced the contrast between flooded and non-flooded regions. The result was a high level of noise in satellite data, which reduced the efficacy of traditional clustering techniques that rely heavily on color or texture.
    - Low Visual Separability of Flooded Areas:
        Flooded regions in Maine lacked clear boundaries and often appeared as scattered dark patches close to river paths. These patterns were hard to distinguish using basic RGB and NDWI overlays alone, particularly when floods occurred in forested or snowy areas.
Feature Engineering:
- For each pixel, we calculated the Euclidean distance to the nearest flowline.
Pixels within a 100-pixel buffer around a river were given more weight in clustering.
This distance matrix was normalized and appended as a fourth feature alongside the traditional RGB channels.
A KMeans clustering model was then trained on these four dimensions.
### Outcome
- Model performance gains were marginal: the distance feature helped localize focus near rivers but didn’t resolve the underlying issue of indistinct flood boundaries in Maine’s noisy imagery.
- Experiments with varying buffer sizes (50–150 pixels) yielded no significant boost in clustering accuracy.
- When applied to Vermont imagery, incorporating distance to flowline as a fourth feature alongside RGB did not yield significant improvement in clustering performance, likely due to the already well-defined flood patterns and higher image clarity in Vermont data.

### Conclusion
The Maine dataset exemplified the difficulty of flood detection in low-signal, low-data environments. While introducing distance-to-flowline as an additional feature proved helpful for directing model attention, it was not sufficient to overcome limitations posed by image noise, data scarcity, and the inherent visual complexity of the region. This experience highlighted the need for further innovation—possibly integrating temporal imagery or supervised learning approaches—in such geospatial challenges.

## Reference
### Data
- [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/)
- [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt)
- [National Water Prediction Service](https://water.noaa.gov/#@=-96.401081,38.1465724,3.3479233&b=topographic&g=obsFcst,1!1!1!1!1!1!1!1!1!1!1!1!1!1!1!0!0!0!0!0,0.5,1!1!1!1!0,0,0&ab=0,0,#D94B4A,1,1,1,#cccccc,1,0,0,#B243B1,1,0,0,#98E09A,1&a=hydrologic,0.35&s=0,0,0.9,0.9&n=false,#72afe9,0.9,0,0.9,0,0.9&p=false,0.75,0,7,0,1,2024,8,15,0&d=0,0,1,1,1,1,1,1,#006EFF,1,#006EFF,1,#006EFF&q=)
- [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/national-hydrography-dataset)
- https://observablehq.com/@martien/fix-circular-references
- https://observablehq.com/@paulplew/mapping-and-filtering-data
- https://snailbones.medium.com/styling-oceans-with-bathymetry-in-maplibre-a326e912e02f
- https://observablehq.com/@neocartocnrs/hello-maplibre
- https://github.com/geotiffjs/geotiff.js/


### Paper
- [A multi-sensor approach for increased measurements of floods and their societal impacts from space](https://www.nature.com/articles/s43247-023-01129-1)
- [Remote sensing for flood inundation mapping using various processing methods with Sentinel-1 and Sentinel-2](https://isprs-archives.copernicus.org/articles/XLVIII-M-1-2023/339/2023/isprs-archives-XLVIII-M-1-2023-339-2023.pdf)
- [GIS and remote sensing based flood risk assessment and mapping: The case of Dikala Watershed in Kobo Woreda Amhara Region, Ethiopia](https://www.sciencedirect.com/science/article/pii/S266597272300020X)
- [Deep Convolutional Neural Network for Flood Extent Mapping Using Unmanned Aerial Vehicles Data](https://www.mdpi.com/1424-8220/19/7/1486)
- [Flood Mapping with Convolutional Neural Networks Using Spatio-Contextual Pixel Information](https://www.mdpi.com/2072-4292/11/19/2331)
