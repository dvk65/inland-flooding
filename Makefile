# collect and preprocess flood event data from STN database
stn_flood_event:
	mkdir -p data/stn
	python -B src/stn.py

# collect and preprocess flood event data (water level above moderate flood stage) from NOAA
gauge_flood_event:
	mkdir -p data/gauge
	python -B src/gauge.py

# conduct EDA on flood event data
eda_flood_event:
	mkdir -p figs
	python -B src/eda_flood_event.py

# collect and preprocess the corresponding sentinel 2 imagery for STN dataset
stn_sentinel2:
	python -B src/stn_sentinel2.py

# conduct EDA on the corresponding sentinel 2 imagery
# eda_stn_sentinel2:
# 	python -B src/eda_stn_sentinel2.py
