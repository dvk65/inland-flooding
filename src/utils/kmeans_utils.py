"""
This script includes the functions used for KMeans clustering algorithm.

This script can be imported as a module and includes the following functions:
    * read_tif - returns the image data and metadata from the TIFF file;
    * apply_cloud_mask - returns the image data with cloud-masked areas assigned to NaN;
    * generate_flowline_mask - returns a mask that identifies the pixels covered by flowlines in the image data;
    * add_image_data - returns a DataFrame with the image and mask data added;
    * preprocess_data - returns a DataFrame with the standardized data;
    * kmeans_clustering_i - returns the clustered image and the inertia;
    * kmeans_clustering = returns the 
"""

import os
import rasterio
import numpy as np
import geopandas as gpd
from utils import global_utils
# from kneed import KneeLocator
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
            sat_image, bounds, tiff_crs, transform, _  = read_tif(image_path) # shape (3, 1200, 1195)
            # sat_image = sat_image/255.0 # normalize
            ndwi_mask, _, _, _, _ = read_tif(ndwi_path)
            cloud_mask, _, _, _, _ = read_tif(cloud_path)
            ndwi_mask = apply_cloud_mask(ndwi_mask, cloud_mask, var='ndwi')
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
        reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
        valid_pixels = ~np.isnan(reshaped_image).any(axis=1)
        valid_data = reshaped_image[valid_pixels]

        # standardize the valid data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(valid_data)

        # reshape and store the scaled data
        scaled_image_full = np.full((reshaped_image.shape[0], scaled_data.shape[1]), np.nan)
        scaled_image_full[valid_pixels] = scaled_data
        scaled_image_final = scaled_image_full.reshape(image.shape[1], image.shape[2], -1).transpose(2, 0, 1)
        scaled_image_list.append(scaled_image_final)
        valid_pixels_list.append(valid_pixels)

    # assign the list of scaled images to the DataFrame column
    df_mod['scaled_image'] = scaled_image_list
    df_mod['valid_pixels'] = valid_pixels_list

    # print the first row for inspection
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])

    return df_mod

def kmeans_clustering_i(image, valid_pixels, init, n_clusters):
    """
    Perform KMeans clustering on the specified image data.

    Args:
        image (numpy.ndarray): The input image data
        n_clusters (int): The number of clusters for KMeans

    Returns:
        numpy.ndarray: The clustered image
        float: The inertia of the clustering result
    """
    reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
    valid_data = reshaped_image[valid_pixels]

    kmeans = KMeans(n_clusters=n_clusters, init=init, n_init='auto', max_iter=300, random_state=42).fit(valid_data)
    inertia = kmeans.inertia_

    # assign labels to valid pixels
    labels = np.full(reshaped_image.shape[0], -1)
    labels[valid_pixels] = kmeans.labels_

    # reshape labels
    clustered_image = labels.reshape(image.shape[1], image.shape[2])

    return clustered_image, inertia

def kmeans_clustering(df, init, n_clusters, condition):
    """
    Perform KMeans clustering on the image datasets.

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        n_clusters (int): The number of clusters for KMeans clustering
        condition (str): Condition to determine the clustering approach ('default', 'optimized', 'optimizing')
    """
    global_utils.print_func_header(f'run {condition} KMeans clustering')
    ids = df['id'].unique()
    clustered_image_list = []
    for current_id in ids:
        id_group = df[df['id'] == current_id] 
        num_images = len(id_group)
        fig, axes = plt.subplots(num_images, 3 + n_clusters, figsize=(15, 5 * num_images))
        fig.suptitle(f'{condition} KMeans Clustering for ID: {current_id}', fontsize=16)
        if num_images == 1:
            axes = np.array([axes])
        for i, (_, row) in enumerate(id_group.iterrows()):
            scaled_image = row['scaled_image']
            sat_image = row['sat_image']
            ndwi_mask = row['ndwi_mask']
            gdf_mask = row['gdf_mask']
            valid_pixels = row['valid_pixels']

            if condition == 'default':
                clustered_image, _ = kmeans_clustering_i(scaled_image, valid_pixels, init, n_clusters)
            elif condition == 'optimize':
                pca_image = row['pca_image']
                clustered_image, _ = kmeans_clustering_i(pca_image, valid_pixels, init, n_clusters)
            clustered_image_list.append(clustered_image)
            cmap = plt.cm.viridis
            cmap.set_bad(color='black')

            axes[i, 0].set_title(f"{row['period']} Original")
            axes[i, 0].imshow(sat_image.transpose(1, 2, 0))

            axes[i, 1].set_title(f"{row['period']} NDWI")
            axes[i, 1].imshow(np.squeeze(ndwi_mask), cmap=cmap)

            axes[i, 2].set_title(f"{row['period']} KMeans")
            axes[i, 2].imshow(clustered_image, cmap=cmap)

            for j in range(n_clusters):
                cluster_mask = (clustered_image == j)
                cluster_image = np.zeros_like(clustered_image, dtype=float)
                cluster_image[cluster_mask] = 1  
                cmap_cluster = ListedColormap(['black', 'white']) 
                axes[i, j + 3].set_title(f"{row['period']} Cluster {j}")
                axes[i, j + 3].imshow(cluster_image, cmap=cmap_cluster, norm=Normalize(vmin=0, vmax=1))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        if condition == 'default':
            plt.savefig(f"figs/kmeans_default/{row['id']}_s2_default.png")
        elif condition == 'optimize':
            plt.savefig(f"figs/kmeans_optimized/{row['id']}_s2_optimized.png")
        plt.close(fig)

        print(f'complete - KMeans clustering on {current_id}')

    if condition == 'default':
        df['clustered_image'] = clustered_image_list
    elif condition == 'optimize':
        df['clustered_image_optimal'] = clustered_image_list

    # print the first row
    print('\nprint out the first row for inspection\n', df.iloc[0])
    return df

def preprocess_image_features(df):
    """
    Combine the image data and other features with StandardScaler() applied

    Args:
        df (pd.DataFrame): The DataFrame with the image data

    Returns:
        pd.DataFrame: The modified DataFrame with the combined data
    """
    global_utils.print_func_header('combine data and standardize/PCA the combined data')
    df_mod = df.copy()
    prepared_data_with_features = []
    pca_n_components_list = []

    # encode the period attribute (before/during/after flood)
    labelencode = LabelEncoder()
    df_mod['period_encoded'] = labelencode.fit_transform(df_mod['period'])

    for _, row in df_mod.iterrows():

        # load the image data and features to be used
        image = row['masked_image']
        ndwi_mask = row['ndwi_mask']
        flowline_mask = row['gdf_mask']
        period_encoded = row['period_encoded']
        valid_pixels = row['valid_pixels']
        # expand dimensions if necessary
        if flowline_mask.ndim == 2:
            flowline_mask = np.expand_dims(flowline_mask, axis=0)

        # todo
        period_channel = np.full(image.shape[1:], period_encoded, dtype=np.float32)
        period_channel = np.expand_dims(period_channel, axis=0)

        # combine data with features
        combined_data = np.concatenate([image, ndwi_mask, flowline_mask, period_channel], axis=0)

        # reshape data
        reshaped_data = combined_data.transpose(1, 2, 0).reshape(-1, combined_data.shape[0])
        valid_data = reshaped_data[valid_pixels]

        # standardize the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(valid_data)

        # determine the optimal number of components for PCA
        pca_test = PCA()
        pca_test.fit(scaled_data)
        explained_variance = np.cumsum(pca_test.explained_variance_ratio_)

        # select the number of components
        n_components = np.argmax(explained_variance >= 0.90) + 1
        pca_n_components_list.append(n_components)

        # apply PCA with selected n_components
        pca = PCA(n_components=n_components)
        scaled_data_pca = pca.fit_transform(scaled_data)

        # create and store the preprocessed data
        pca_image = np.full((reshaped_data.shape[0], scaled_data_pca.shape[1]), np.nan)
        pca_image[valid_pixels] = scaled_data_pca
        pca_image = pca_image.reshape(image.shape[1], image.shape[2], -1).transpose(2, 0, 1)
        prepared_data_with_features.append(pca_image)

    df_mod['n_components'] = pca_n_components_list
    df_mod['pca_image'] = prepared_data_with_features

    print('selected n_components among all the images:\n', df_mod['n_components'].unique())

    # plot the explained variance
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(explained_variance) + 1), explained_variance, marker='o', linestyle='--')
    plt.title('Cumulative Explained Variance by Number of Components')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.grid()
    plt.savefig('figs/kmeans_optimizing/pca_n_components.png')
    plt.close()

    # print the first row
    print('\nprint out the first row for inspection\n', df_mod.iloc[0])

    return df_mod


def select_n_clusters(df, init):
    """
    Perform KMeans clustering on the image datasets to find the optimal number of clusters.
    """
    global_utils.print_func_header('identify the optimal number of clusters')
    cluster_list = [2, 3, 4, 5, 6]
    inertia_result = []
    clustered_images = []

    test_image = df['pca_image']
    valid_pixels = df['valid_pixels']
    for i in cluster_list:
        print(f'current - {i}')
        clustered_image, inertia = kmeans_clustering_i(test_image, valid_pixels, init, i)
        inertia_result.append(inertia)
        clustered_images.append(clustered_image)

    plt.figure(figsize=(10, 6))
    plt.plot(cluster_list, inertia_result, marker='o', linestyle='--')
    plt.title('Elbow Method')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig(f'figs/kmeans_optimizing/elbow_plot.png')
    plt.close()

    # kl = KneeLocator(cluster_list, inertia_result, curve='convex', direction='decreasing')
    # optimal_clusters = kl.elbow

    # print(f'selected n_clusters: {optimal_clusters}')