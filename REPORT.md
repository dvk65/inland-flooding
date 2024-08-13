# Report
This project focus on developing an algorithm for automated assessment of inland flooding from satellite observations. Specifically, this algorithm collects satellite images corresponding to before-, during-, and after-flood events and applies the K-means clustering technique to identify flooded areas. While the project initially targeted Maine, it has been expanded to include other states with similar flood characteristics due to limited observations in Maine.

The ultimate goal is to enhance the accuracy of flooded area assessments, with potential applications in enhancing flood detection using drone measurements.

## Data
The approach integrates the datasets described in the table below:
| **Name** | **Source** | **Description** | **Format** | **Links** |
|---|---|---|---|---|
| [High-water marks](https://www.usgs.gov/special-topics/water-science-school/science/high-water-marks-and-flooding) | [STN flood event data](https://stn.wim.usgs.gov/STNDataPortal/) | validated flood event observations from USGS | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [High-water levels](https://www.weather.gov/aprfc/terminology) | [USGS Water Data Services](https://waterdata.usgs.gov/nwis/rt) | real-time gauge water levels above moderate flood stage | CSV | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Sentinel-2 satellite images](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2) | [Sentinel-2 Level-2A](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | satellite images corresponding to the areas of interest and timeframes defined by high-water marks and levels | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Cloud and Shadow](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) masks | [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) | cloud and shadow pixels to be dropped | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Normalized Difference Water Index](https://eos.com/make-an-analysis/ndwi/) masks | [Example](https://medium.com/@melqkiades/water-detection-using-ndwi-on-google-earth-engine-2919a9bf1951) | water body pixels defined by NDWI index to refine the algorithm's accuracy | GeoTIFF | [Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |
| [Flowlines](https://www.usgs.gov/ngp-standards-and-specifications/national-hydrography-dataset-nhd-data-dictionary-feature-classes) | [National Hydrography Dataset](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) | Flowing water data used to enhance analysis and improve algorithm performance | Shapefile | 1.[Report>](REPORT.md)<br>[Guide>](GUIDE.md)<br>[Data>](https://drive.google.com/drive/folders/1HnRyw0KoQEsYrYD9Uid-N08lBs0q-1jo?usp=sharing) |

## Method
1. Collect flood event data from two sources: high-water marks available through the USGS STN Flood Event Data Portal and high-water levels extracted from real-time gauge data provided by USGS Water Data Services;
2. Collect satellite images corresponding to before-, during-, and after-flood event data;
3. Apply the K-means clustering technique to identify flooded areas
<img src="figs/workflow.png" width="800" alt="workflow">


## Result and Discussion

### Flood Event Data
Firstly, we can check the flood event data summary table below:
| \ | **High-water marks** | **High-water levels** |
|---|---|---|
| **overview** | 889 observations | 218 observations |
| **top 3 counts by event** | 2023 July MA NY VT Flood (641)<br>2018 March Extratropical Cyclone (115)<br>2018 January Extratropical Cyclone (81)| 2023-12 (64)<br>2023-07 (27)<br>2024-01 (18) |
| **top 3 counts by state** | VT (646)<br>MA (282)<br>CT (72) | CT (57)<br>VT (56)<br>ME (40) |
| **countplot** | <img src="figs/countplot/countplot_stn.png" width="500" alt="STN Flood Event Distribution">| <img src="figs/countplot/countplot_gauge.png" width="500" alt="Gauge Flood Event Distribution"> |
| **map based on top 1 by state** | <img src="figs/map/map_VT_stn_gauge.png" width="500" alt="VT Flood Event Distribution"> | <img src="figs/map/map_CT_stn_gauge.png" width="500" alt="CT Flood Event Distribution"> |

**Discussion**
- In Vermont, the 2023 July MA NY VT Flood event has the highest number of data points. Many of these points are clustered close to each other, with minimal overlap between STN and gauge data;
- In Connecticut, there are fewer data points. STN data points are primarily located along the coast, while gauge data points are concentrated near the river. There is no overlap between the STN and gauge data.

**Note**
- No exact dates are assigned to the flood events. Therefore, to collect and distinguish the satellite imagery before/during/after flood events, I explored online reports to define the dates. This process will be included in [GUIDE](GUIDE.md);
- High-water levels depends on the moderate flood stage threshold which can be adjusted.
- (map color similarity)

### Sentinel-2 True Color Imagery, Cloud Masks, NDWI Masks, and Flowline Masks
The filtered dataset consists of 102 Sentinel-2 True Color images, each paired with corresponding masks for clouds, shadows, NDWI, and flowlines. 

* [True Color](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/composites/) - band combination of red (B04), green (B03), and blue (B02)

#### Sentinel-2 True Color Imagery
Initially, 379 Sentinel-2 True Color images, along with their corresponding CLOUD and NDWI masks, were downloaded. These images represented 17 different flood events and were collected using 1107 flood event observations. However, after visualizing the first 5 observations, some images were found to be unsuitable for analysis (specific reasons to be added). Following this evaluation, the July 2023 flood event was selected for further analysis and K-means clustering.

The refined dataset of ideal Sentinel-2 True Color images comprises 102 images, with 25 collected during flood events. Upon further exploration, 10 of these images were identified to show significant flooded areas through visual inspection. The IDs of these images are 44909, 44929, 45067, 45237, 45321, 45358, 45427, 45501, MNTM3_114, and TMVC3_39. 

Below is a table showing some of the collected images.
| \ | **Figure** | **Note** |
|---|---|---|
| **44909** | <img src="figs/s2_ready/44909_s2_ready.png"> | from STN high-water marks |
| **44929** | <img src="figs/s2_ready/44929_s2_ready.png">| from STN high-water marks |
| **45358** | <img src="figs/s2_ready/45358_s2_ready.png"> | from STN high-water marks |
| **TMVC3_39** | <img src="figs/s2_ready/TMVC3_39_s2_ready.png"> | from Gauge high-water levels |
| **Some of removed ids and images** | <img src="figs/s2_selected/CLMM3_97_s2_selected.png"> <img src="figs/s2_vis_inspect/AUBM1_59_s2.png">| In the top image set, The image with date 20230706 is dropped due to the cloud cover. In the bottom image set, even though the river is brown. The color similarity indicates that it's not an ideal image for this project. |

####  Cloud Masks and NDWI Masks (from Earth Engine)
When downloading Sentinel-2 images, [s2cloudless](https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless) is utilized to extract the cloud and shadow mask. This step is included to drop the cloud and shadow pixels in Kmeans clustering algorithm. The cloud masked created using the s2cloudless algorithm can be affected by high reflectance which is demonstrated below.

Below is a table showing the cloud masks.
| \ | **True Color** | **Cloud Mask** |
|---|---|---|
| **44909** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2.png"> | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_cloud.png"> |
| **44929** | <img src="figs/s2/44929_20230711T153821_20230711T154201_T18TXN_VIS_s2.png"> | <img src="figs/s2/44929_20230711T153821_20230711T154201_T18TXN_VIS_cloud.png"> |


Also, NDWI mask is collected when downloading Sentinel-2 images. After that, the NDWI threshold is selected by comparison. Below is a table showing the threshold selection. The selected threshold is -0.1.
| \ | **NDWI thresholds**| **True Color** |
|---|---|---|
| **44909** | <img src="figs/s2_ndwi/44909_20230711T153821_20230711T154201_T18TXP_NDWI_test.png"> | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2.png"> |
| **44929** | <img src="figs/s2_ndwi/44929_20230711T153821_20230711T154201_T18TXN_NDWI_test.png"> | <img src="figs/s2/44929_20230711T153821_20230711T154201_T18TXN_VIS_s2.png"> |
| **45358** | <img src="figs/s2_ndwi/45358_20230711T153821_20230711T154201_T18TXP_NDWI_test.png"> | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2.png"> |

#### Flowline Masks
Flowlines from NHD is introduced to help identify the flooded areas and enhance KMeans clustering performance. In this project, the focus is major rivers based on the visual inspection. Therefore, the major rivers are selected from flowlines. However, there might be a better approach to idetify major rivers. 

| \ | **Flowline**| **Major River** |
|---|---|---|
| **44909** | <img src="figs/flowline_no_filter.png"> | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> |

### KMeans Clustering Result

Below is the result of 44909
| \ | **True Color**| **Result** |
|---|---|---|
| **Default** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/44909_20230711_default.png"> |
| **PCA** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/44909_20230711_pca_i.png"> |
| **PCA with flowline** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/44909_20230711_pca_flowline_i.png"> |
| **PCA with NDWI** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/44909_20230711_pca_ndwi_i.png"> |
| **PCA with flowline and NDWI** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/44909_20230711_pca_features_i.png"> |

Below is the result of 45358
| \ | **True Color**| **Result** |
|---|---|---|
| **Default** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/45358_20230711_default.png"> |
| **PCA** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/45358_20230711_pca_i.png"> |
| **PCA with flowline** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/45358_20230711_pca_flowline_i.png"> |
| **PCA with NDWI** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/45358_20230711_pca_ndwi_i.png"> |
| **PCA with flowline and NDWI** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_s2_flowline.png"> | <img src="figs/kmeans_clusters/45358_20230711_pca_features_i.png"> |

### Comparison between Target Cluster (Flooded Area) and NDWI

| \ | **NDWI**| **Best Cluster** | **Pixels** |
|---|---|---|---|
| **44909** | <img src="figs/s2/44909_20230711T153821_20230711T154201_T18TXP_VIS_ndwi.png"> | <img src="figs/kmeans_clusters/44909_20230711_pca_ndwi_i.png"> | NDWI: 37389<br>Target Cluster: 36039 |
| **45358** | <img src="figs/s2/45358_20230711T153821_20230711T154201_T18TXP_VIS_ndwi.png"> | <img src="figs/kmeans_clusters/45358_20230711_pca_ndwi_i.png"> | NDWI: 36823<br>Target Cluster: 36715 |
