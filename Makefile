# collect and preprocess flood event data from STN database
collect_stn:
	mkdir -p data/df_stn
	python -B src/stn.py

# collect and preprocess flood event data (water level above moderate flood stage) from NOAA
collect_gauge:
	mkdir -p data/df_gauge
	python -B src/gauge.py

# conduct EDA on flood event data
analyze_stn_gauge:
	mkdir -p figs/stn_gauge
	python -B src/analyze_stn_gauge.py

# collect and preprocess the corresponding sentinel 2 imagery for STN dataset
collect_sentinel2:
	mkdir -p data/img_sentinel2
	python -B src/sentinel2.py

# conduct EDA on the corresponding sentinel 2 imagery
analyze_image:
	mkdir -p data/df_sentinel2 figs/image_group_by_id figs/image_selected figs/image_before_during_after_abs_diff
	python -B src/analyze_image.py

#run KMeans algorithm
run_kmeans:
	mkdir -p figs/kmeans_default figs/kmeans_optimized
	python -B src/kmeans.py