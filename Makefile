# collect and preprocess flood event data from STN database
stn:
	mkdir -p data/df_stn
	python -B src/stn.py

# collect and preprocess flood event data (water level above moderate flood stage) from NOAA
gauge:
	mkdir -p data/df_gauge
	python -B src/gauge.py

# conduct EDA on flood event data
eda_flood_event:
	mkdir -p figs/countplot figs/map
	python -B src/eda_flood_event.py

# collect and preprocess the corresponding sentinel 2 imagery
s2:
	mkdir -p data/img_s2
	python -B src/s2.py

# conduct EDA on the corresponding sentinel 2 imagery
eda_s2:
	mkdir -p data/df_s2 figs/s2_raw_vis_by_id figs/s2_event_selected figs/s2_cleaned figs/s2_ndwi_test figs/s2 data/nhd
	python -B src/eda_s2.py

# run KMeans algorithm
kmeans:
	mkdir -p data/df_kmeans figs/kmeans_optimizing figs/kmeans_default figs/kmeans_pca figs/kmeans_ndwi_pca figs/kmeans_flowline_pca figs/kmeans_features_pca
	python -B src/kmeans.py

# run experiment (currently code used to explore the flowline features)
experiment:
	python -B src/experiment.py

# use .tif from data folder for GitHub page
page:
	gdalwarp -t_srs EPSG:3857 -r near data/img_s2/2023-07/45358_20230711T153821_20230711T154201_T18TXP_VIS.tif data/45358_webmap.tif
	gdal2tiles.py -p mercator -z 0-18 -w none data/45358_webmap.tif docs/45358_tiles

# use flood_event.csv for GitHub page
csvjson:
	python -c " \
	import csv, json; \
	with open('data/flood_event.csv', 'r') as f: \
	    reader = csv.DictReader(f); \
	    rows = list(reader); \
	with open('docs/flood_event.json', 'w') as f: \
	    json.dump(rows, f, indent=4) \
	"