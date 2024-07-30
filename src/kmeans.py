"""
This script segments images to identify water bodies, 
allowing us to assess flooded areas during flood events.

This script includes the following steps:
    * step 1 - load the necessary datasets;
    * step 2 - prepare for KMeans clustering;
    * step 3 - run the default KMeans clustering algorithm on the processed images;
    * step 4 - optimize the algorithm by ...;
    * step 5 - evaluate the result.
"""

# import libraris
import pandas as pd
from utils import kmeans_utils

# step 1 - load the dataframe
df = pd.read_csv('data/image_kmeans.csv')

# step 2 - preparation
n_clusters = 3

# step 3 - run default KMeans (Currently testing on the first 5 ids)
kmeans_utils.kmeans_clustering_all(df[:5], n_clusters, 'default')

# step 4 - optimize KMeans
kmeans_utils.kmeans_clustering_all(df[:5], n_clusters, 'optimizing')

# step 5 - run optimized KMeans but function incomplete (TO BE ADDED - Currently testing on the first 5 ids)
# kmeans_utils.kmeans_clustering_all(df[:5], n_clusters, 'Optimized)

# step 6 - evaluate the result (TO BE ADDED)