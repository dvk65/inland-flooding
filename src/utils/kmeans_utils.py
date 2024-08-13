"""
This script includes the functions used for KMeans clustering algorithm.

This script can be imported as a module and includes the following functions:
    * read_tif - return the image data and metadata from the TIFF file;
    * generate_flowline_mask - return a mask that identifies the pixels covered by flowlines in the image data;
    * add_image_data - return a DataFrame with the image and mask data added;
    * preprocess_data - return a DataFrame with the standardized image data and valid pixels;
    * kmeans_clustering_i - return the clustered image and inertia for specified image;
    * find_sharpest_slope_point - return the optimal number of clusters defined by the sharpest slope point;
    * identify_flood_cluster - return the lable of cluster that has the greatest overlap with the NDWI mask
    * kmeans_clustering_default - return the result of default KMeans clustering optimization;
    * kmeans_optimization_individual_pca_features - return the result of KMeans clustering optimization by introducing NDWI/flowline mask and applying PCA;
    * plot_clustered_result - plot the clustered image and individual clusters separately;
    * plot_evaluation_metrics - plot and save evaluation metrics (cumulative explained variance and elbow method) for KMeans clustering;
"""

import os
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
from utils import global_utils
from kneed import KneeLocator
import matplotlib.pyplot as plt
from shapely.geometry import box
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from rasterio.features import geometry_mask
from sklearn.preprocessing import StandardScaler
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

def generate_flowline_mask(flowline_gdf, image_shape, transform):
    """
    Create a mask for identifying the pixels covered by flowlines

    Args:
        flowline_gdf (pd.GeoDataFrame): A GeoDataFrame representing the flowline geometries to be masked
        image_shape (tuple): A tuple representing the shape of the image
        transform (Affine): The affine transformation mapping the image's pixel coordinates to geographic coordinates

    Returns:
        np.ndarray: A array representing the flowline mask (flowline - 1; other areas - 0)

    Notes:
        https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html
    """
    mask = geometry_mask([geometry for geometry in flowline_gdf.geometry],
                         out_shape=image_shape,
                         transform=transform,
                         invert=True)  
    return mask.astype(np.int32)

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
    ndwi_mask_dict = {}
    sat_image_dict = {}
    masked_image_dict = {}
    flowline_mask_dict = {}
    ndwi_pixels_dict = {}
    # load the dictionary mapping full state names to their abbreviations
    area_abbr_list = global_utils.area_abbr_list

    area_exist = df_mod['state'].unique().tolist()
    for i in area_exist:

        # filter the dataset for the specific state
        df_i = df_mod[df_mod['state'] == i].copy()
        state_full = [name for name, abbr in area_abbr_list.items() if abbr == i][0]

        # load the flowline shapefile and extract major rivers
        major_river = [558]
        shp_path = f'data/nhd/{state_full}/Shape/NHDFlowline.shp'
        flowline = gpd.read_file(shp_path)
        major_rivers = flowline[(flowline['ftype'].isin(major_river)) & (flowline['lengthkm'] >= 0.6)]
        for index, row in df_i.iterrows():

            # load image and mask
            image_path = os.path.join(row['dir'], row['filename'])
            ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
            cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
            sat_image, bounds, tiff_crs, transform, _  = read_tif(image_path) # shape (3, 1200, 1195) <- (channels, height, width)
            ndwi_mask, _, _, _, _ = read_tif(ndwi_path)
            ndwi_mask = global_utils.read_ndwi_tif(ndwi_path)
            ndwi_mask = global_utils.apply_cloud_mask(ndwi_mask, cloud_path)
            masked_image = global_utils.apply_cloud_mask(sat_image, cloud_path)

            ndwi_pixels = np.sum(ndwi_mask == 1)

            # extract the flowline mask
            if major_rivers.crs != tiff_crs:
                major_rivers = major_rivers.to_crs(tiff_crs)

            bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
            filtered_flowline = major_rivers[major_rivers.geometry.intersects(bbox)]
            flowline_mask = generate_flowline_mask(filtered_flowline, sat_image.shape[1:], transform)

            # add the np.ndarray data to the list
            ndwi_mask_dict[index] = ndwi_mask
            sat_image_dict[index] = sat_image
            masked_image_dict[index] = masked_image
            flowline_mask_dict[index] = flowline_mask
            ndwi_pixels_dict[index] = ndwi_pixels
        print(f"complete - add the image data for observations in {i}")

    df_mod['ndwi_mask'] = df_mod.index.map(ndwi_mask_dict)
    df_mod['sat_image'] = df_mod.index.map(sat_image_dict)
    df_mod['masked_image'] = df_mod.index.map(masked_image_dict)
    df_mod['flowline_mask'] = df_mod.index.map(flowline_mask_dict)
    df_mod['ndwi_pixels'] = df_mod.index.map(ndwi_pixels_dict)

    global_utils.describe_df(df_mod, 'df with standardized image data')

    # print the first row
    print('\nprint out the first  for inspection\n', df_mod.iloc[0])

    result_df = pd.DataFrame({
        'id': df_mod['filename'],
        'ndwi_pixels': df_mod['ndwi_pixels'],
    })

    return df_mod, result_df

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

def find_sharpest_slope_point(cluster_list, inertia_result):
    """
    Find the point with the sharpest slope in the inertia plot

    Args:
        cluster_list (list): A list of the number of clusters
        inertia_result (list): The corresponding inertia values

    Returns:
        int: The optimal number of clusters defined by the sharpest slope point
    """
    slopes = np.diff(inertia_result) # calculate the slope
    sharpest_slope_index = np.argmax(np.abs(slopes)) # identify the index
    return cluster_list[sharpest_slope_index + 1] # return the optimal number of clusters

def identify_flood_cluster(unique_labels, clustered_image, ndwi_mask_flat):
    """
    Identify the cluster with the greatest possibility of representing flooded area

    Args:
        unique_labels (array): A array of unique cluster labels identified
        clustered_images (np.ndarray): A 2D array representing the clustered image
        ndwi_mask_flat (np.ndarray): A flattened binary array indicating the presence of water

    Returns:
        int: The lable of cluster that has the greatest overlap with the NDWI mask
    """
    flood_cluster = None
    overlap_threshold = 0
    for cluster in unique_labels:
        cluster_match = (clustered_image == cluster)
        overlap = np.sum(cluster_match & (ndwi_mask_flat == 1))
        if overlap > overlap_threshold:
            overlap_threshold = overlap
            flood_cluster = cluster
    return flood_cluster

def kmeans_clustering_default(df, init, n_clusters, condition):
    """
    Perform default KMeans clustering on the image datasets

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        init (str): The specified initialization method for KMeans
        n_clusters (int): The number of clusters for KMeans clustering
        condition (str): The string used to label the executed KMeans clustering setting
    Returns:
        pd.DataFrame: A dataframe storing the results
    """
    global_utils.print_func_header(f'run default KMeans clustering')

    df_mod = df.copy()
    cluster_pixel_count_list = []
    flood_cluster_list = []

    for _, row in df_mod.iterrows():
        scaled_image = row['scaled_image']
        sat_image = row['sat_image']
        valid_pixels = row['valid_pixels']
        ndwi_mask = row['ndwi_mask']

        ndwi_mask_flat = ndwi_mask.flatten()[valid_pixels]
        clustered_image, _ = kmeans_clustering_i(scaled_image, init, n_clusters)
        unique_labels, counts = np.unique(clustered_image, return_counts=True)
        cluster_pixel_count = {f'cluster_{label}': int(count) for label, count in zip(unique_labels, counts)}
        cluster_pixel_count_list.append(cluster_pixel_count)

        # automatically identify the flood cluster
        flood_cluster = identify_flood_cluster(unique_labels, clustered_image, ndwi_mask_flat)
        flood_cluster_list.append(flood_cluster)

        filename = f"{row['id']}_{row['date']}_default"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, n_clusters, filename, condition)
        print(f"complete - KMeans clustering on {row['filename']}")

    # print the first row
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])

    result_df = pd.DataFrame({
        'id': df_mod['filename'],
        'cluster_pixel_count_default': cluster_pixel_count_list,
        'n_clusters_default': [n_clusters] * len(df_mod),
        'flooded_cluster_default': flood_cluster_list
    })

    result_df.to_csv('data/df_kmeans/df_kmeans_default.csv', index=False)

    return result_df

def kmeans_optimization_individual_pca_features(df, init, condition):
    """
    Optimize KMeans clustering by introducing NDWI/flowline mask and applying PCA

    Args:
        df (pd.DataFrame): The dataframe with image data used to do optimization
        init (str): The specified initialization method for KMeans
        condition (str): The string used to determine what type of optimization is applied
    
    Returns:
        pd.DataFrame: A dataframe storing the results 
    """
    global_utils.print_func_header(f'optimize image individually with {condition}')
    df_mod = df.copy()

    # create list to store information
    pca_n_components_list = []
    n_clusters_list = []
    cluster_pixel_count_list = []
    flood_cluster_list = []
    explained_variance_list = []
    inertia_result_list = []

    for _, row in df_mod.iterrows():

        # load the image data and features to be used
        scaled_image = row['scaled_image']
        ndwi_mask = row['ndwi_mask']
        flowline_mask = row['flowline_mask']
        valid_pixels = row['valid_pixels']
        sat_image = row['sat_image']

        # flatten the data
        ndwi_mask_flat = ndwi_mask.flatten()[valid_pixels]
        flowline_mask_flat = flowline_mask.flatten()[valid_pixels]

        # check which optimization to be selected
        if condition == 'flowline_pca':
            non_image_features = flowline_mask_flat.reshape(-1, 1)
        elif condition == 'ndwi_pca':
            non_image_features = ndwi_mask_flat.reshape(-1, 1)
        elif condition == 'features_pca':
            non_image_features = np.column_stack([ndwi_mask_flat, flowline_mask_flat])
        else:
            non_image_features = None

        # define the data used to PCA and KMeans clustering
        if non_image_features is not None:
            scaler = StandardScaler()
            non_image_features_scaled = scaler.fit_transform(non_image_features)
            combined_data = np.column_stack([scaled_image, non_image_features_scaled])
        else:
            combined_data = scaled_image

        # test PCA and determine the optimal n_components
        pca_test = PCA()
        pca_test.fit(combined_data)
        explained_variance = np.cumsum(pca_test.explained_variance_ratio_)
        explained_variance_list.append(str(explained_variance.tolist()))

        n_components = np.argmax(explained_variance >= 0.90) + 1
        pca_n_components_list.append(n_components)

        # apply PCA with the optimal n_components
        pca = PCA(n_components=n_components)
        scaled_data_pca = pca.fit_transform(combined_data)

        # determine the optimal n_clusters using elbow method
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
        inertia_result_list.append(str(inertia_result))

        # run KMeans
        clustered_image, _ = kmeans_clustering_i(scaled_data_pca, init, optimal_clusters)
        unique_labels, counts = np.unique(clustered_image, return_counts=True)
        cluster_pixel_count = {f'cluster_{label}': int(count) for label, count in zip(unique_labels, counts)}
        cluster_pixel_count_list.append(cluster_pixel_count)

        # automatically identify the flood cluster by checking the overlap between cluster and NDWI
        flood_cluster = identify_flood_cluster(unique_labels, clustered_image, ndwi_mask_flat)
        flood_cluster_list.append(flood_cluster)

        # add necessary plot
        filename = f"{row['id']}_{row['date']}_{condition}_i"
        plot_clustered_result(clustered_image, valid_pixels, sat_image.shape, optimal_clusters, filename, condition)

        print(f"complete - optimize image individually with {condition} {row['filename']}")

    print('selected n_components among all the images:\n', set(pca_n_components_list))
    print('selected n_clusters among all the images:\n', set(n_clusters_list))

    # create a DataFrame to store results
    result_df = pd.DataFrame({
            'id': df_mod['filename'],
            f'cluster_pixel_count_{condition}_i': cluster_pixel_count_list,
            f'n_clusters_{condition}_i': n_clusters_list,
            f'n_components_{condition}_i': pca_n_components_list,
            f'flooded_cluster_{condition}_i': flood_cluster_list,
            f'explained_variance_{condition}_i': explained_variance_list,
            f'inertia_result_{condition}_i': inertia_result_list,
            f'n_clusters_list_{condition}_i': [str(cluster_list)] * len(df_mod)
        })

    result_df.to_csv(f'data/df_kmeans/df_kmeans_{condition}_i.csv', index=False)
    return result_df

def plot_clustered_result(cluster_image, valid_pixels, original_shape, n_clusters, file, dir_ending):
    """
    Plot the clustered image and individual clusters separately

    Args:
        cluster_image (np.ndarray): An array containing the cluster labels assigned to valid pixels
        valid_pixels (np.ndarray): An array representing the valid pixels
        original_shape (tuple): The original shape of the image
        n_clusters (int): The number of clusters
        file (str): The filename of the file to be saved
        dir_ending (str): A string used as part of directory name
    """
    name = file.split('/')[-1]
    _, height, width = original_shape
    full_image = np.full(height * width, -1)
    full_image[valid_pixels] = cluster_image
    full_image = full_image.reshape(height, width)

    cluster_colors = plt.cm.get_cmap('viridis', n_clusters)
    cmap_clustered = ListedColormap(cluster_colors.colors)
    cmap_clustered.set_bad(color='gray')

    full_image_masked = np.ma.masked_where(full_image == -1, full_image)
    fig, axes = plt.subplots(1, n_clusters + 1, figsize=(4 * (n_clusters + 1), 5))
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
    plt.savefig(f'figs/kmeans_{dir_ending}/{file}.png')
    plt.close()

def plot_evaluation_metrics(explained_variance, cluster_list, inertia_result, file):
    """
    Plot and save evaluation metrics (cumulative explained variance and elbow method) for KMeans clustering

    Args:
        explained_variance (list of float): A list of float numbers representing cumulative explained variance ratios by the number of PCA components
        cluster_list (list of int): A list of integer representing the number of clusters used in KMeans clustering
        inertia_result (list of float): A list of inertia values corresponding to the number clusters
        file (str): The basename used to save the plot
    """

    # plot the cumulative explained variance by the number of PCA components
    plt.figure(figsize=(10, 10))
    plt.plot(range(1, len(explained_variance) + 1), explained_variance, marker='o', linestyle='--')
    plt.title(f'cumulative explained variance by number of components\n{file}')
    plt.xlabel('number of components')
    plt.ylabel('cumulative explained variance')
    plt.grid()
    plt.savefig(f'figs/kmeans_optimizing/{file}_n_components.png')
    plt.close()

    # plot the inertia results using the elbow method for determining the optimal number of clusters
    plt.figure(figsize=(10, 10))
    plt.plot(cluster_list, inertia_result, marker='o', linestyle='--')
    plt.title(f'elbow method\n{file}')
    plt.xlabel('number of clusters')
    plt.ylabel('inertia')
    plt.grid()
    plt.savefig(f'figs/kmeans_optimizing/{file}_elbow.png')
    plt.close()