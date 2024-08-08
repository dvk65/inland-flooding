"""
This script includes the functions used for KMeans clustering algorithm.

This script can be imported as a module and includes the following functions:
    * read_tif - returns the image data and metadata from the TIFF file;
    * apply_cloud_mask - returns the image data with cloud-masked areas assigned to NaN;
    * generate_flowline_mask - returns a mask that identifies the pixels covered by flowlines in the image data;
    * add_image_data - returns a DataFrame with the image and mask data added;
    * preprocess_data - returns a DataFrame with the standardized data;
    * kmeans_clustering_i - unfinished
    * kmeans_clustering - unfinished
"""

import os
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
from utils import global_utils, nhd_utils
from kneed import KneeLocator
import matplotlib.pyplot as plt
from shapely.geometry import box
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from rasterio.features import geometry_mask
from sklearn.preprocessing import StandardScaler, LabelEncoder
from matplotlib.colors import Normalize, ListedColormap

def read_tif(file_path):
    """
    Read a TIFF file and return its image data and metadata

    Args:
        file_path (str) : The path to the TIFF file to be read

    Returns:
        data (numpy.ndarray): The image data read from the TIFF file
        bounds (rasterio.coords.BoundingBox): The spatial boundary of the image
        crs (rasterio.crs.CRS): The coordinate reference system
        transform (affine.Affine): The transformation matrix for transforming of coordinates from image pixel (row, col) to 
                                   and from geographic/projected (x, y) coordinates
        profile (dict): Metadata and profile information of the TIFF file
    """
    with rasterio.open(file_path) as src:
        return src.read(), src.bounds, src.crs, src.transform, src.profile

def apply_cloud_mask(image, cloud_mask, var=None):
    """
    Apply a cloud mask to the specified image by setting the masked areas to NaN.

    Args:
        image (numpy.ndarray): The input image data
        cloud_mask (numpy.ndarray): The cloud mask to be applied
    
    Returns:
        numpy.ndarray: The image with cloud-masked areas set to NaN
    """

    # assign NaN to cloud-masked areas
    masked_image = image.copy().astype(np.float32)

    if var == 'ndwi':
        masked_image[:, cloud_mask[0] == 1] = 0
    else:
        masked_image[:, cloud_mask[0] == 1] = np.nan

    return masked_image

def generate_flowline_mask(flowline_gdf, image_shape, transform):
    """
    Create a mask for identifying the pixels covered by flowlines

    Args:
        flowline_gdf (pd.GeoDataFrame): A GeoDataFrame representing the flowline geometries to be masked
        image_shape (tuple): A tuple representing the shape of the image
        transform (Affine): The affine transformation mapping the image's pixel coordinates to geographic coordinates

    Returns:
        np.ndarray: A array representing the flowline mask (flowline - 1.0; other areas - 0.0)

    Notes:
        https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html
    """
    mask = geometry_mask([geometry for geometry in flowline_gdf.geometry],
                         out_shape=image_shape,
                         transform=transform,
                         invert=True)  
    return mask.astype(np.float32)

def add_image_data(df):
    '''
    Add the image and mask data (np.ndarray) to the image DataFrame

    Args:
        df (pd.DataFrame): The existing DataFrame storing the image and its metadata

    Returns:
        pd.DataFrame: The modified DataFrame with the image and mask data (np.ndarray) added
    '''
    global_utils.print_func_header('add the image data')
    df_mod = df.copy()
    # create lists to store the data
    ndwi_mask_list = []
    cloud_mask_list = []
    sat_image_list = []
    masked_image_list = []
    gdf_mask_list = []

    # load the dictionary mapping full state names to their abbreviations
    area_abbr_list = global_utils.area_abbr_list

    area_exist = df_mod['state'].unique().tolist()
    for i in area_exist:

        # filter the dataset for the specific state
        df_i = df_mod[df_mod['state'] == i]
        state = i
        state_full = [name for name, abbr in area_abbr_list.items() if abbr == state][0]

        # load the flowline shapefile
        shp_path = f'data/nhd/{state_full}/Shape/NHDFlowline.shp'
        gdf = gpd.read_file(shp_path)
        for _, row in df_i.iterrows():

            # load image and mask
            image_path = os.path.join(row['dir'], row['filename'])
            ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
            cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
            sat_image, bounds, tiff_crs, transform, _  = read_tif(image_path) # shape (3, 1200, 1195) <- (channels, height, width)
            ndwi_mask, _, _, _, _ = read_tif(ndwi_path)
            cloud_mask, _, _, _, _ = read_tif(cloud_path)
            ndwi_mask = nhd_utils.read_ndwi_tif(ndwi_path)
            ndwi_mask = nhd_utils.apply_cloud_mask(ndwi_mask, cloud_path)
            masked_image = apply_cloud_mask(sat_image, cloud_mask)

            # extract the flowline mask
            if gdf.crs != tiff_crs:
                gdf = gdf.to_crs(tiff_crs)

            bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
            filtered_gdf = gdf[gdf.geometry.intersects(bbox)]
            flowline_mask = generate_flowline_mask(filtered_gdf, sat_image.shape[1:], transform)

            # add the np.ndarray data to the list
            ndwi_mask_list.append(ndwi_mask)
            cloud_mask_list.append(cloud_mask)
            sat_image_list.append(sat_image)
            masked_image_list.append(masked_image)
            gdf_mask_list.append(flowline_mask)
        print(f"complete - add the image data for observations in {i}")

    df_mod['ndwi_mask'] = ndwi_mask_list
    df_mod['cloud_mask'] = cloud_mask_list
    df_mod['sat_image'] = sat_image_list
    df_mod['masked_image'] = masked_image_list
    df_mod['gdf_mask'] = gdf_mask_list

    global_utils.describe_df(df_mod, 'df with standardized image data')

    # print the first row
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])
    return df_mod

def preprocess_data(df):
    df_mod = df.copy()
    global_utils.print_func_header('preprocess the image data')
    scaled_image_list = []
    valid_pixels_list = []

    for _, row in df_mod.iterrows():
        # load the valid image data
        image = row['masked_image']

        # (channels, height, width) -> (num_pixels = height * width, channels)
        reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0]) # convert the image data into a format where each row is a pixel and each column is a channel value (feature) -> flatten into a 2D array for clustering
        valid_pixels = ~np.isnan(reshaped_image).any(axis=1) # store rows (pixels) with no NaN values (check if any channel value in a pixel is NaN)
        valid_data = reshaped_image[valid_pixels]

        # standardize the valid data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(valid_data)

        # store the scaled data and valid pixel
        scaled_image_list.append(scaled_data)
        valid_pixels_list.append(valid_pixels)

    # assign the list of scaled images to the DataFrame column
    df_mod['scaled_image'] = scaled_image_list
    df_mod['valid_pixels'] = valid_pixels_list

    # print the first row for inspection
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])

    return df_mod

def kmeans_clustering_i(image, init, n_clusters):
    """
    Perform KMeans clustering on the specified image data.

    Args:
        image (numpy.ndarray): The input image data
        n_clusters (int): The number of clusters for KMeans

    Returns:
        numpy.ndarray: The clustered image
        float: The inertia of the clustering result
    """
    kmeans = KMeans(n_clusters=n_clusters, init=init, n_init='auto', max_iter=300, random_state=42).fit(image)
    inertia = kmeans.inertia_
    labels = kmeans.labels_
    return labels, inertia

def plot_clustered_result(cluster_image, valid_pixels, original_shape, n_clusters, file):
    name = file.split('/')[-1]
    _, height, width = original_shape
    full_image = np.full(height * width, -1)
    full_image[valid_pixels] = cluster_image
    full_image = full_image.reshape(height, width)

    cluster_colors = plt.cm.get_cmap('viridis', n_clusters)
    cmap_clustered = ListedColormap(cluster_colors.colors)
    cmap_clustered.set_bad(color='gray')

    full_image_masked = np.ma.masked_where(full_image == -1, full_image)
    fig, axes = plt.subplots(1, n_clusters + 1, figsize=(20, 8))

    fig.suptitle(f'KMeans result - {name}')
    
    axes[0].set_title(f'Clustered Image')
    im = axes[0].imshow(full_image_masked, cmap=cmap_clustered, interpolation='nearest')
    cbar = plt.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04, ticks=np.arange(n_clusters))
    cbar.ax.tick_params(labelsize=8)
    axes[0].axis('off')
    
    for j in range(n_clusters):
        cluster_mask = (full_image == j)
        cluster_image_display = np.zeros_like(full_image, dtype=float)
        cluster_image_display[cluster_mask] = 1
        
        cmap_cluster = ListedColormap(['black', 'white'])
        axes[j + 1].set_title(f"Cluster {j}")
        axes[j + 1].imshow(cluster_image_display, cmap=cmap_cluster, norm=Normalize(vmin=0, vmax=1))
        axes[j + 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(file)
    plt.close()

def kmeans_clustering_default(df, init, n_clusters, condition):
    """
    Perform KMeans clustering on the image datasets.

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        n_clusters (int): The number of clusters for KMeans clustering
        condition (str): Condition to determine the clustering approach ('default', 'optimized', 'optimizing')
    """
    global_utils.print_func_header(f'run {condition} KMeans clustering')

    df_mod = df.copy()
    clustered_image_list = []

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        sat_image = row['sat_image']
        valid_pixels = row['valid_pixels']

        file = f"figs/kmeans_default/{row['id']}_{row['date']}_{row['period']}_s2_default.png"
        clustered_image, _ = kmeans_clustering_i(scaled_image, init, n_clusters)

        clustered_image_list.append(clustered_image)
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, n_clusters, file)

    print(f"complete - KMeans clustering on {row['filename']}")

    # print the first row
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])

def find_sharpest_slope_point(cluster_list, inertia_result):
    """
    Find the point with the sharpest slope in the inertia plot
    """
    slopes = np.diff(inertia_result)
    sharpest_slope_index = np.argmax(np.abs(slopes))
    return cluster_list[sharpest_slope_index + 1]

def kmeans_optimization_individual_pca(df, init):
    global_utils.print_func_header('optimize image individually with pca')
    df_mod = df.copy()
    pca_n_components_list = []
    explained_variance_list = []
    n_clusters_list = []
    clustered_image_list = []

    for _, row in df_mod.iterrows():

        # load the image data and features to be used
        sat_image = row['sat_image']
        scaled_image = row['scaled_image']
        valid_pixels = row['valid_pixels']

        # combine the standardized features with the scaled image
        combined_data = scaled_image

        # determine the optimal number of components for PCA
        pca_test = PCA()
        pca_test.fit(combined_data)
        explained_variance = np.cumsum(pca_test.explained_variance_ratio_)
        explained_variance_list.append(explained_variance)

        # select the number of components
        n_components = np.argmax(explained_variance >= 0.90) + 1
        pca_n_components_list.append(n_components)

        # apply PCA with selected n_components
        pca = PCA(n_components=n_components)
        scaled_data_pca = pca.fit_transform(combined_data)

        cluster_list = [2, 3, 4, 5, 6]
        inertia_result = []
        for i in cluster_list:
            _, inertia = kmeans_clustering_i(scaled_data_pca, init, i)
            inertia_result.append(inertia)
        kl = KneeLocator(cluster_list, inertia_result, curve='convex', direction='decreasing')
        optimal_clusters = kl.elbow
        if optimal_clusters is not None and not np.isnan(optimal_clusters):
            optimal_clusters = int(optimal_clusters)
        else:
            optimal_clusters = find_sharpest_slope_point(cluster_list, inertia_result)
        n_clusters_list.append(int(optimal_clusters))

        # plot clustered image
        clustered_image, _ = kmeans_clustering_i(scaled_data_pca, init, optimal_clusters)
        clustered_image_list.append(clustered_image)
        file = f"figs/kmeans_optimized/{row['id']}_{row['date']}_{row['period']}_s2_pca_i.png"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, optimal_clusters, file)

    # plot the explained variance
    print('selected n_components among all the images:\n', set(pca_n_components_list))
    print('selected n_clusters among all the images:\n', set(n_clusters_list))

def kmeans_optimization_individual_pca_features(df, init):
    global_utils.print_func_header('optimize image individually with pca and combined features')
    df_mod = df.copy()
    pca_n_components_list = []
    n_clusters_list = []


    for _, row in df_mod.iterrows():

        # load the image data and features to be used
        scaled_image = row['scaled_image']
        ndwi_mask = row['ndwi_mask']
        flowline_mask = row['gdf_mask']
        valid_pixels = row['valid_pixels']
        sat_image = row['sat_image']

        ndwi_mask_flat = ndwi_mask.flatten()[valid_pixels]
        flowline_mask_flat = flowline_mask.flatten()[valid_pixels]

        non_image_features = ndwi_mask_flat.reshape(-1, 1)
        scaler = StandardScaler()
        non_image_features_scaled = scaler.fit_transform(non_image_features)

        combined_data = np.column_stack([scaled_image, non_image_features_scaled])

        pca_test = PCA()
        pca_test.fit(combined_data)
        explained_variance = np.cumsum(pca_test.explained_variance_ratio_)

        n_components = np.argmax(explained_variance >= 0.90) + 1
        pca_n_components_list.append(n_components)

        pca = PCA(n_components=n_components)
        scaled_data_pca = pca.fit_transform(combined_data)

        cluster_list = [2, 3, 4, 5, 6]
        inertia_result = []
        for i in cluster_list:
            _, inertia = kmeans_clustering_i(scaled_data_pca, init, i)
            inertia_result.append(inertia)
        kl = KneeLocator(cluster_list, inertia_result, curve='convex', direction='decreasing')
        optimal_clusters = kl.elbow
        if optimal_clusters is not None and not np.isnan(float(optimal_clusters)):
            optimal_clusters = int(optimal_clusters)
        else:
            optimal_clusters = int(find_sharpest_slope_point(cluster_list, inertia_result))
        n_clusters_list.append(optimal_clusters)

        clustered_image, _ = kmeans_clustering_i(scaled_data_pca, init, optimal_clusters)
        file = f"figs/kmeans_optimized/{row['id']}_{row['date']}_{row['period']}_s2_pca_features_i.png"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, optimal_clusters, file)

    print('selected n_components among all the images:\n', set(pca_n_components_list))
    print('selected n_clusters among all the images:\n', set(n_clusters_list))


def kmeans_optimization_all_pca(df, init):
    global_utils.print_func_header('optimize image together with pca')
    df_mod = df.copy()
    combined_data_list = []

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        combined_data_list.append(scaled_image)

    all_combined_data = np.vstack(combined_data_list)

    pca_test = PCA()
    pca_test.fit(all_combined_data)
    explained_variance = np.cumsum(pca_test.explained_variance_ratio_)

    n_components = np.argmax(explained_variance >= 0.90) + 1

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(explained_variance) + 1), explained_variance, marker='o', linestyle='--')
    plt.title('Cumulative Explained Variance by Number of Components')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.grid()
    plt.savefig('figs/kmeans_optimizing/pca_n_components_pca_all.png')
    plt.close()

    pca = PCA(n_components=n_components)
    all_combined_data_pca = pca.fit_transform(all_combined_data)

    cluster_list = [2, 3, 4, 5, 6]
    inertia_result = []
    for i in cluster_list:
        _, inertia = kmeans_clustering_i(all_combined_data_pca, init, i)
        inertia_result.append(inertia)

    plt.figure(figsize=(10, 6))
    plt.plot(cluster_list, inertia_result, marker='o', linestyle='--')
    plt.title('Elbow Method')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig('figs/kmeans_optimizing/elbow_plot_pca_all.png')
    plt.close()

    kl = KneeLocator(cluster_list, inertia_result, curve='convex', direction='decreasing')
    optimal_clusters = kl.elbow
    if optimal_clusters is not None and not np.isnan(optimal_clusters):
        optimal_clusters = int(optimal_clusters)
    else:
        optimal_clusters = find_sharpest_slope_point(cluster_list, inertia_result)

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        valid_pixels = row['valid_pixels']
        sat_image = row['sat_image']

        scaled_data_pca = pca.transform(scaled_image)

        clustered_image, _ = kmeans_clustering_i(scaled_data_pca, init, optimal_clusters)
        file = f"figs/kmeans_optimized/{row['id']}_{row['date']}_{row['period']}_s2_pca_all.png"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, optimal_clusters, file)

    print('Selected n_components among all the images:\n', n_components)
    print('Selected n_clusters among all the images:\n', optimal_clusters)


def kmeans_optimization_all_pca_features(df, init):
    """
    resource limitation - killed (need to be revised)
    """
    global_utils.print_func_header('optimize image together with pca and combined features')
    df_mod = df.copy()
    combined_data_list = []
    
    scaler = StandardScaler()  

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        ndwi_mask = row['ndwi_mask']
        flowline_mask = row['gdf_mask']
        valid_pixels = row['valid_pixels']
        
        ndwi_mask_flat = ndwi_mask.flatten()[valid_pixels]
        flowline_mask_flat = flowline_mask.flatten()[valid_pixels]

        non_image_features = ndwi_mask_flat.reshape(-1, 1)
        non_image_features_scaled = scaler.fit_transform(non_image_features)
        
        combined_data = np.column_stack([scaled_image, non_image_features_scaled])
        combined_data_list.append(combined_data)

        del ndwi_mask_flat, flowline_mask_flat, non_image_features, non_image_features_scaled, combined_data

    all_combined_data = np.vstack(combined_data_list)
    del combined_data_list  

    pca_test = PCA()
    pca_test.fit(all_combined_data)
    explained_variance = np.cumsum(pca_test.explained_variance_ratio_)

    n_components = np.argmax(explained_variance >= 0.90) + 1

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(explained_variance) + 1), explained_variance, marker='o', linestyle='--')
    plt.title('Cumulative Explained Variance by Number of Components')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.grid()
    plt.savefig('figs/kmeans_optimizing/pca_n_components_pca_features_all.png')
    plt.close()

    pca = PCA(n_components=n_components)
    all_combined_data_pca = pca.fit_transform(all_combined_data)
    del all_combined_data  

    cluster_list = [2, 3, 4, 5, 6]
    inertia_result = []
    for i in cluster_list:
        _, inertia = kmeans_clustering_i(all_combined_data_pca, init, i)
        inertia_result.append(inertia)

    plt.figure(figsize=(10, 6))
    plt.plot(cluster_list, inertia_result, marker='o', linestyle='--')
    plt.title('Elbow Method')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig('figs/kmeans_optimizing/elbow_plot_pca_features_all.png')
    plt.close()

    kl = KneeLocator(cluster_list, inertia_result, curve='convex', direction='decreasing')
    optimal_clusters = kl.elbow
    if optimal_clusters is not None and not np.isnan(optimal_clusters):
        optimal_clusters = int(optimal_clusters)
    else:
        optimal_clusters = find_sharpest_slope_point(cluster_list, inertia_result)

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        ndwi_mask = row['ndwi_mask']
        flowline_mask = row['gdf_mask']
        valid_pixels = row['valid_pixels']
        sat_image = row['sat_image']

        ndwi_mask_flat = ndwi_mask.flatten()[valid_pixels]
        flowline_mask_flat = flowline_mask.flatten()[valid_pixels]

        non_image_features = ndwi_mask_flat.reshape(-1, 1)
        non_image_features_scaled = scaler.transform(non_image_features)  

        combined_data = np.column_stack([scaled_image, non_image_features_scaled])

        scaled_data_pca = pca.transform(combined_data)

        del ndwi_mask_flat, flowline_mask_flat, non_image_features, non_image_features_scaled, combined_data

        clustered_image, _ = kmeans_clustering_i(scaled_data_pca, init, optimal_clusters)
        file = f"figs/kmeans_optimized/{row['id']}_{row['date']}_{row['period']}_s2_pca_features_all.png"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, optimal_clusters, file)

        del scaled_data_pca, clustered_image

    print('Selected n_components among all the images:\n', n_components)
    print('Selected n_clusters among all the images:\n', optimal_clusters)