"""
This script includes the functions used to segment images. 

This file can be imported as a module and contains the following functions:
    * read_tif - returns the data and profile information of the specified TIFF file.
    * apply_cloud_mask - returns the image with a cloud mask.
    * initialize_centroids - returns the initialized centroids for KMeans clustering.
    * kmeans_clustering - returns the clustered image
    * kmeans_clustering_all - plot the kmeans result
"""
import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from matplotlib.colors import Normalize, ListedColormap

def read_tif(file_path):
    """
    Read a TIFF file and returns its data and profile information.

    Args:
        file_path (str) : The path to the TIFF file to be read.

    Returns:
        data (numpy.ndarray): The image data read from the TIFF file.
        profile (dict): Metadata and profile information of the TIFF file.
    """
    with rasterio.open(file_path) as src:
        return src.read(), src.profile

def apply_cloud_mask(image, cloud_mask):
    """
    Apply a cloud mask to the specified image by setting the masked areas to NaN

    Args:
        image (numpy.ndarray): The input image data
        cloud_mask (numpy.ndarray): The cloud mask to be applied
    
    Returns:
        numpy.ndarray: the image with cloud-masked areas set to NaN
    """
    if cloud_mask.ndim == 2:
        # expand dimensions if cloud_mask is 2D
        cloud_mask = np.expand_dims(cloud_mask, axis=0)
    
    # convert the image to float32
    masked_image = image.copy().astype(np.float32)

    # set the masked areas to NaN
    masked_image[:, cloud_mask[0] == 1] = np.nan
    return masked_image

def initialize_centroids(images, n_clusters):
    """
    Initialize centroids for KMeans clustering to ensure the consistency between the clustered image results

    Args:
        images (list): a list of image arrays to be used for initializing centroids
        n_clusters (int): the number of clusters for KMeans clustering

    Returns:
        numpy.array: the initialized centroids for KMeans clustering
    """
    all_valid_data = []
    for image in images:
        # reshape the image
        reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
        
        # identify valid pixels (remove NaNs)
        valid_pixels = ~np.isnan(reshaped_image).any(axis=1)

        # extract valid data
        valid_data = reshaped_image[valid_pixels]
        all_valid_data.append(valid_data)
    
    # combine valid data
    all_valid_data = np.vstack(all_valid_data)
    
    # perform KMeans clustering to initialize centroids
    kmeans = KMeans(n_clusters=n_clusters,
                    init='k-means++',
                    n_init='auto',
                    max_iter=300,
                    random_state=42).fit(all_valid_data)
    return kmeans.cluster_centers_

def kmeans_clustering(image, n_clusters, init_centroids):
    """
    Perform KMeans clustering on the specified image data

    Args:
        image (numpy.ndarray): the input image data
        n_clusters (int): the number of clusters for KMeans
        init_centroids (numpy.ndarray, optional): pre-initialized centroids for KMeans

    Returns:
        numpy.ndarray: the clustered image
    """
    # reshape the image
    reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])

    # identify and extract valid data
    valid_pixels = ~np.isnan(reshaped_image).any(axis=1)
    valid_data = reshaped_image[valid_pixels]

    # run KMeans
    kmeans = KMeans(n_clusters=n_clusters, init=init_centroids, n_init='auto', max_iter=300, random_state=42).fit(valid_data)
    
    # initialize an array for labeling the pixels
    labels = np.full(reshaped_image.shape[0], -1)

    # assign labels to valid pixels
    labels[valid_pixels] = kmeans.labels_

    # reshape the labels back to the original image dimensions
    clustered_image = labels.reshape(image.shape[1], image.shape[2])
    return clustered_image

def kmeans_clustering_all(df, n_clusters, optimize_bool):
    """
    Perform KMeans clustering on the image datasets

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        n_clusters (int): The number of clusters for KMeans clustering
        optimize_bool (bool): Flag to determine whether to optimize 
    """
    periods = ['before', 'during', 'after']
    all_images = {period: [] for period in periods}
    all_cloud_masks = {period: [] for period in periods}
    all_ndwi_masks = {period: [] for period in periods}
    
    for period in periods:
        for index, row in df.iterrows():
            file_name = row[period]
            vis_dir = row['dir']
            file_path = os.path.join(vis_dir, file_name)
            sat_image, _ = read_tif(file_path)
            cloud_file_path = os.path.join(vis_dir.rstrip('/') + '_CLOUD', file_name.replace("_VIS.tif", "_CLOUD.tif"))
            ndwi_file_path = os.path.join(vis_dir.rstrip('/') + '_NDWI', file_name.replace("_VIS.tif", "_NDWI.tif"))
            cloud_mask, _ = read_tif(cloud_file_path)
            ndwi_mask, _ = read_tif(ndwi_file_path)
            cloud_mask = cloud_mask[0]
            masked_image = apply_cloud_mask(sat_image, cloud_mask)
            ndwi_mask = apply_cloud_mask(ndwi_mask, cloud_mask)
            all_images[period].append(sat_image)  
            all_cloud_masks[period].append(masked_image) 
            all_ndwi_masks[period].append(ndwi_mask)

    if optimize_bool:
        # To be added
        print('TO be added')
    else:
        all_images_combined = all_cloud_masks['before'] + all_cloud_masks['during'] + all_cloud_masks['after']
        centroids = initialize_centroids(all_images_combined, n_clusters)

    for index, row in df.iterrows():
        clustered_results = {period: None for period in periods}
        
        for period in periods:
            masked_image = all_cloud_masks[period][index]
            clustered_image = kmeans_clustering(masked_image, n_clusters, init_centroids=centroids)
            clustered_results[period] = clustered_image

        fig, axes = plt.subplots(3, 3 + n_clusters, figsize=(18, 18))
        fig.suptitle(f"ID: {row['id']}", fontsize=16)

        for i, period in enumerate(periods):
            original_image = all_images[period][index] 
            clustered_image = clustered_results[period]
            ndwi_mask = all_ndwi_masks[period][index]

            cmap = plt.cm.viridis
            cmap.set_bad(color='black')

            axes[i, 0].set_title(f'{period} Original')
            axes[i, 0].imshow(original_image.transpose(1, 2, 0))

            axes[i, 1].set_title(f'{period} NDWI')
            axes[i, 1].imshow(np.squeeze(ndwi_mask), cmap=cmap)

            axes[i, 2].set_title(f'{period} KMeans')
            axes[i, 2].imshow(clustered_image, cmap=cmap)

            for j in range(n_clusters):
                cluster_mask = (clustered_image == j)
                cluster_image = np.zeros_like(clustered_image, dtype=float)
                cluster_image[cluster_mask] = 1  
                cmap_cluster = ListedColormap(['black', 'white']) 
                axes[i, j + 3].set_title(f'{period} KMeans Cluster {j}')
                axes[i, j + 3].imshow(cluster_image, cmap=cmap_cluster, norm=Normalize(vmin=0, vmax=1))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        if optimize_bool:
            plt.savefig(f"figs/kmeans_optimized/{row['id']}_sentinel2_kmeans_optimized.png")
            plt.close(fig)
        else:
            plt.savefig(f"figs/kmeans_default/{row['id']}_sentinel2_kmeans_default.png")
            plt.close(fig)


