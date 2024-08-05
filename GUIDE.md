# Environment Setup, Tools/Platforms, and Dataset Documentation

This document is a brief guide to help users set up the required environment, utilize the tools and platforms utilized, and understand the datasets in this project. 

## Table of Contents
- [Environment Setup](#environment-setup)
    - [Creating the environment from the environment.yml](#setting-up-the-environment-from-the-environmentyml)
    - [Google Earth Engine Setup](#google-earth-engine-setup)
- [Tools and Platforms](#tools-and-platforms)
- [Dataset Documentation](#dataset-documentation)

## Environment Setup
### Setting up the environment from the environment.yml
1. use the terminal to create the environment from the environment.yml:
```
conda env create -f environment.yml
```

2. activate the environment (the environment's name can be found in the yml file):
```
conda activate flood
```

### Google Earth Engine Setup
Google Earth Engine has a guide about [setting up Earth Engine enabled Cloud Project](https://developers.google.com/earth-engine/cloud/earthengine_cloud_project_setup). Below is a step-by-step demonstration of the approach I selected to use Google Earth Engine.

#### step 1 - create a cloud project
We can create a Google Cloud Project using this [link](https://console.cloud.google.com/projectcreate) or clicking on the button in the official setup guide. 
![create a project](./figs/guide/create_project.png)
#### step 2 - enable the Earth Engine API
To enable the Earth Engine API, we can click on the button (Enable the Earth Engine API) in the offical setup guide or search for Earth Engine API in APIs & Services section. 
![enable api](./figs/guide/enable_api.png)
To use this API, we may need credentials. If you haven't done so, you will see a warning after clicking on the Enable button. 
![create credentials](./figs/guide/create_credentials.png)
Clicking on the CREATE CREDENTIALS button, we'll move to the section of creating credentials. 
![credential type](./figs/guide/set_credential_type.png)
![consent screen](./figs/guide/consent_screen.png)
![client id](./figs/guide/client_id.png)
#### step 3 - register Earth Engine
To use Earth Engine, we need to register the project [here](https://code.earthengine.google.com/register). 
![get started](./figs/guide/register_project.png)
![select use](./figs/guide/select_use.png)
![select project](./figs/guide/select_project.png)
#### step 4 - fetch credentials using gcloud
When running `make s2`, you will receive the following output:
![login](./figs/guide/login.png)


1. create a Cloud project named flood-demo:
2. create credentials before using Google Earth Engine API:
3. enable Google Earth Engine API in APIs & Services:
4. enter authorization code when running `make s2` for the first time:

## Tools and Platforms

## Dataset Documentation

