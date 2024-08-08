"""
This script segments images, allowing us to assess flooded areas during flood events.

This script includes the following steps:
    * step 1 - load the necessary datasets;
    * step 2 - add the image data to df;
    * step 3 - run the default KMeans clustering algorithm on the processed images;
    * step 4 - optimize the algorithm by ...;
    * step 5 - run optimized KMeans;
    * step 6 - evaluation
"""

# import libraris
import time
import pandas as pd
import numpy as np
from utils import kmeans_utils

# track the runtime
start = time.time()
print('\nSTART - KMEANS CLUSTERING MODEL\n')

# set variable
default_n_clusters = 3
batch_size = 10

# step 1 - load the dataframe
df = pd.read_csv('data/s2.csv')

# batch processing to avoid killed

# step 2 - add the image data to df (consider Batch Processing)
df_mod  = kmeans_utils.add_image_data(df)

# step 3 - preprocess data (do not store the reshaped scaled data)
df_scaled = kmeans_utils.preprocess_data(df_mod)

df_flood = df_scaled[df_scaled['period'] == 'during flood']
print(len(df_flood))

# step 4 - run default KMeans
init = 'k-means++'
# kmeans_utils.kmeans_clustering_default(df_scaled, init, default_n_clusters, 'default')

# step 5 - optimize KMeans
kmeans_utils.kmeans_optimization_individual_pca(df_scaled, init)
kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init)
# kmeans_utils.kmeans_optimization_all_pca(df_flood, init)
# kmeans_utils.kmeans_optimization_all_pca_features(df_flood[:10], init) # face 

# step 7 - evaluate the result (TO BE ADDED)
# compare with ndwi
# calculate the area

print('\nCOMPLETE - KMEANS CLUSTERING MODEL\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')