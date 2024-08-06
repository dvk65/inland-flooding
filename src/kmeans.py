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
df_mod  = kmeans_utils.add_image_data(df[:3])

# step 3 - preprocess data (do not store the reshaped scaled data)
df_scaled = kmeans_utils.preprocess_data(df_mod)

# # step 4 - run default KMeans
init = 'k-means++'
df_kmeans_default = kmeans_utils.kmeans_clustering(df_scaled, init, default_n_clusters, 'default')

# # step 5 - optimize KMeans
df_features_pca = kmeans_utils.preprocess_image_features(df_kmeans_default)

# # select the ideal init

# # select the optimal n_clusters
kmeans_utils.select_n_clusters(df_features_pca.iloc[0], init) 

# # step 6 - run optimized KMeans but function incomplete (TO BE ADDED - Currently testing on the first 5 ids)
n_cluster_optimize = 4
df_kmeans_optimize = kmeans_utils.kmeans_clustering(df_features_pca, init, n_cluster_optimize, 'optimize')

# step 7 - evaluate the result (TO BE ADDED)
# compare with ndwi
# compare with water using the perpendicular line to estimate river width (water body)
# silhouette score
# calculate the area
# how about the change of color before and during flood

print('\nCOMPLETE - KMEANS CLUSTERING MODEL\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')