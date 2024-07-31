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
	mkdir -p figs/flood_event
	python -B src/eda_flood_event.py

# collect and preprocess the corresponding sentinel 2 imagery for STN dataset
s2:
	mkdir -p data/img_s2
	python -B src/s2.py

# conduct EDA on the corresponding sentinel 2 imagery
eda_s2:
	mkdir -p data/df_s2 figs/s2_vis_inspect 
	python -B src/eda_s2.py

# run KMeans algorithm
kmeans:
	mkdir -p figs/kmeans_default figs/kmeans_optimizing figs/kmeans_optimized
	python -B src/kmeans.py

# evaluation
evaluation:

# run test
test:
	mkdir -p figs/test
	python -B src/test.py
