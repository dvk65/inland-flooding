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

# step 1 - prepare the dataframes
# step 1.1 - load the dataframe storing the image metadata
df = pd.read_csv('data/s2.csv')

# step 1.2 - extract the rows for which the `id` has during flood lable (remove the flood event observations that has no image during flood)
flood_ids = df[df['period'] == 'during flood']['id'].unique()
df_id_flood = df[df['id'].isin(flood_ids)].copy()

# step 2 - add the image data to df
df_mod, result_df_ndwi  = kmeans_utils.add_image_data(df_id_flood[:3])

# step 3 - preprocess data
df_scaled = kmeans_utils.preprocess_data(df_mod)

# step 4 - run default KMeans
init = 'k-means++'
results_df_default = kmeans_utils.kmeans_clustering_default(df_scaled, init, default_n_clusters, 'default')

# step 5 - optimize KMeans using different combinations
# step 5.1 - optimize KMeans by applying PCA to each image
result_df_pca_i = kmeans_utils.kmeans_optimization_individual_pca(df_scaled, init, 'pca', check=False)

# step 5.2 - optimize KMeans by adding flowline as a feature and applying PCA to each image
result_df_pca_flowline = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'flowline_pca', check=False)

# step 5.3 - optimize KMeans by adding NDWI as a feature and applying PCA to each image
result_df_pca_ndwi = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'ndwi_pca', check=False)

# step 5.4 - optimize KMeans by adding flowline and NDWI as features and applying PCA to each image
result_df_pca_features = kmeans_utils.kmeans_optimization_individual_pca_features(df_scaled, init, 'features_pca', check=False)

# step 6 - evaluate the result
# result_df_combined = pd.merge(results_df_default, result_df_pca_i, on='id')
# result_df_combined = pd.merge(result_df_combined, result_df_pca_flowline, on='id')
# result_df_combined = pd.merge(result_df_combined, result_df_pca_ndwi, on='id')
# result_df_combined = pd.merge(result_df_combined, result_df_pca_features, on='id')
# result_df_combined = pd.merge(result_df_combined, result_df_ndwi, on='id')
# result_df_combined.to_csv('data/kmeans.csv', index=False)

print('\nCOMPLETE - KMEANS CLUSTERING MODEL\n')

# calculate the runtime
end = time.time()
print(f'\nRUNTIME: {round((end - start) / 60, 2)} minutes')