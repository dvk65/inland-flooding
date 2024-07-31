import os
import rasterio
import numpy as np
from utils import global_utils
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from matplotlib.colors import Normalize, ListedColormap

def read_tif(file_path):
    """
    Read a TIFF file and return its data and profile information.

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
    Apply a cloud mask to the specified image by setting the masked areas to NaN.

    Args:
        image (numpy.ndarray): The input image data
        cloud_mask (numpy.ndarray): The cloud mask to be applied
    
    Returns:
        numpy.ndarray: The image with cloud-masked areas set to NaN
    """
    if cloud_mask.ndim == 2:
        cloud_mask = np.expand_dims(cloud_mask, axis=0)
    masked_image = image.copy().astype(np.float32)
    masked_image[:, cloud_mask[0] == 1] = np.nan
    return masked_image

def add_image_data(df):
    '''
    Add the image data and save to df
    '''
    global_utils.print_func_header('add the image data')
    ndwi_mask_list = []
    cloud_mask_list = []
    sat_image_list = []
    masked_image_list = []
    for _, row in df.iterrows():
        image_path = os.path.join(row['dir'], row['filename'])
        ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
        cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
        sat_image, _ = read_tif(image_path)
        ndwi_mask, _ = read_tif(ndwi_path)
        cloud_mask, _ = read_tif(cloud_path)
        cloud_mask = cloud_mask[0]
        ndwi_mask = apply_cloud_mask(ndwi_mask, cloud_mask)
        masked_image = apply_cloud_mask(sat_image, cloud_mask)
        ndwi_mask_list.append(ndwi_mask)
        cloud_mask_list.append(cloud_mask)
        sat_image_list.append(sat_image)
        masked_image_list.append(masked_image)
    df['ndwi_mask'] = ndwi_mask_list
    df['cloud_mask'] = cloud_mask_list
    df['sat_image'] = sat_image_list
    df['masked_image'] = masked_image_list
    global_utils.describe_df(df, 'df with standardized image data')
    return df

def kmeans_clustering(image, n_clusters, condition):
    """
    Perform KMeans clustering on the specified image data.

    Args:
        image (numpy.ndarray): The input image data
        n_clusters (int): The number of clusters for KMeans
        condition (str): Condition 

    Returns:
        numpy.ndarray: The clustered image
        float: The inertia of the clustering result
    """
    reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
    valid_pixels = ~np.isnan(reshaped_image).any(axis=1)
    valid_data = reshaped_image[valid_pixels]

    # standardize the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(valid_data)
    pca = PCA(n_components=0.90)
    scaled_data = pca.fit_transform(scaled_data)

    kmeans = KMeans(n_clusters=n_clusters, n_init='auto', max_iter=300, random_state=42).fit(scaled_data)
    inertia = kmeans.inertia_
    # assign labels to valid pixels
    labels = np.full(reshaped_image.shape[0], -1)
    labels[valid_pixels] = kmeans.labels_

    # reshape labels
    clustered_image = labels.reshape(image.shape[1], image.shape[2])

    return clustered_image, inertia

def kmeans_clustering_default(df, n_clusters, condition):
    """
    Perform KMeans clustering on the image datasets.

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        n_clusters (int): The number of clusters for KMeans clustering
        condition (str): Condition to determine the clustering approach ('default', 'optimized', 'optimizing')
    """
    global_utils.print_func_header('run default KMeans clustering')
    ids = df['id'].unique()
    clustered_image_list = []
    for current_id in ids:
        id_group = df[df['id'] == current_id] 
        num_images = len(id_group)
        fig, axes = plt.subplots(num_images, 3 + n_clusters, figsize=(15, 5 * num_images))
        fig.suptitle(f'KMeans Clustering for ID: {current_id}', fontsize=16)
        if num_images == 1:
            axes = np.array([axes])
        for i, (index, row) in enumerate(id_group.iterrows()):
            masked_image = row['masked_image']
            sat_image = row['sat_image']
            ndwi_mask = row['ndwi_mask']
            clustered_image, _ = kmeans_clustering(masked_image, n_clusters, condition)
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

        plt.savefig(f"figs/kmeans_default/{row['id']}_s2_default.png")
        plt.close(fig)

        print(f'complete - KMeans clustering on {current_id}')
    df['clustered_image'] = clustered_image_list
    return df

def select_n_clusters(df, condition):
    """
    Perform KMeans clustering on the image datasets to find the optimal number of clusters.
    """
    global_utils.print_func_header('identify the optimal number of clusters')
    cluster_list = [2, 3, 4, 5, 6]
    inertia_result = []
    clustered_images = []

    test_image = df['masked_image']
    for i in cluster_list:
        print(f'current - {i}')
        clustered_image, inertia = kmeans_clustering(test_image, i, condition=condition)
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