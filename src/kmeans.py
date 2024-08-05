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
from utils import kmeans_utils

# track the runtime
start = time.time()
print('\nSTART - KMEANS CLUSTERING MODEL\n')

# set variable
default_n_clusters = 3

# step 1 - load the dataframe
df = pd.read_csv('data/s2.csv')

# step 2 - add the image data to df
df_mod  = kmeans_utils.add_image_data(df)

# step 3 - preprocess data
df_scaled = kmeans_utils.preprocess_data(df_mod)

# step 4 - run default KMeans
init = 'k-means++'
df_kmeans_default = kmeans_utils.kmeans_clustering_default(df_mod, init, default_n_clusters, 'default')

# step 5 - optimize KMeans
kmeans_utils.select_n_clusters(df_mod.iloc[0], init, 'default')

# step 6 - run optimized KMeans but function incomplete (TO BE ADDED - Currently testing on the first 5 ids)

# step 7 - evaluate the result (TO BE ADDED)

print('\nCOMPLETE - KMEANS CLUSTERING MODEL\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')