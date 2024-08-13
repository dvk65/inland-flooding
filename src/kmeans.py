"""
This script segments images, allowing us to assess flooded areas during flood events.

This script includes the following steps:
    * step 1 - load the necessary datasets;
    * step 2 - add the image data to df;
    * step 3 - standardize data and extract valid pixels;
    * step 4 - run default KMeans clustering algorithm with n_clusters = 3;
    * step 5 - optimize KMeans using different combinations;
    * step 6 - evaluation by comparing the target cluster (flooded area) pixels and NDWI water body pixels.
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

# step 1 - load the dataframe storing the image metadata
df = pd.read_csv('data/s2_id_with_flood.csv')

# step 2 - add the image data to df
df_mod, result_df_ndwi  = kmeans_utils.add_image_data(df)

# step 3 - preprocess data
df_scaled = kmeans_utils.preprocess_data(df_mod)

# step 4 - run default KMeans
init = 'k-means++'
results_df_default = kmeans_utils.kmeans_clustering_default(df_scaled, init, default_n_clusters, 'default')

# step 5 - optimize KMeans using different combinations
# step 5.1 - optimize KMeans by applying PCA to each image
result_df_pca_i = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'pca')

# step 5.2 - optimize KMeans by adding flowline as a feature and applying PCA to each image
result_df_pca_flowline = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'flowline_pca')

# step 5.3 - optimize KMeans by adding NDWI as a feature and applying PCA to each image
result_df_pca_ndwi = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'ndwi_pca')

# step 5.4 - optimize KMeans by adding flowline and NDWI as features and applying PCA to each image
result_df_pca_features = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'features_pca')

# step 6 - save the KMeans result
result_df_combined = pd.merge(results_df_default, result_df_pca_i, on='id')
result_df_combined = pd.merge(result_df_combined, result_df_pca_flowline, on='id')
result_df_combined = pd.merge(result_df_combined, result_df_pca_ndwi, on='id')
result_df_combined = pd.merge(result_df_combined, result_df_pca_features, on='id')
result_df_combined = pd.merge(result_df_combined, result_df_ndwi, on='id')
result_df_combined.to_csv('data/kmeans.csv', index=False)

# step 7 - check the explained variance and elbow method for specified image if interested (currently )
print('dataset storing KMeans result:\n')
result_df_combined.info()

# result_df_combined['']

print('\nCOMPLETE - KMEANS CLUSTERING MODEL\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')