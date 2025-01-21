# Spatial Accessibility of America

<!-- # Manuscript code and data -->
<!-- <h3 style="color: #06f"> Towards a generalized accessibility measure for transportation equity and efficiency</h3> -->

**Contributors**: [Dr. Rajat Verma](https://rvanxer.github.io), [Shagun Mittal](https://umnilab.github.io/profiles/Shagun_Mittal), [Prof. Satish V. Ukkusuri](https://umnilab.github.io)

<img src="fig/Cover figure.png" width=1200>

## Abstract
In geography and transportation planning, "spatial accessibility" is defined as the ease and extent to which opportunities (such as jobs, education, healthcare, etc.) can be visited within some travel constraints.

This is a highly parametric dataset containing values of spatial accessibility measured by combinations of multiple measurement methods, travel modes, types of opportunity (such as jobs and different types of points of interest (POIs)), and travel time thresholds. This includes both cumulative opportunities types of measures as well as floating catchment area (FCA)-based competition metrics, including an in-house developed FCA metric aimed for cross-modal comparison. Based on these combinations, a total of 675 accessibility values are computed for each zone at three US Census administrative levels – county, census tract, and block group (BG) – for the 50 most populous urban areas of the United States.

Additionally, the dataset also includes the travel time matrix (TTM) files for each of these urban areas by three travel modes – driving, walking, and bicycling.

The motivation, data collection and preparation process, and technical validation are explained in detail in a [draft manuscript](https://purdue0-my.sharepoint.com/:w:/r/personal/verma99_purdue_edu/Documents/Purdue/Projects/SPR%204711/Papers/Access%20Data/Access%20Data%20-%20v1.docx?d=wa24c7665308d40dabd6a222918a60c17&csf=1&web=1&e=JFDXJj).

## Download link
The accessibility data for the 50 most populous urban areas can be downloaded from the following link:

> **Google Drive**: [Spatial Accessibility of America (SAA)](https://drive.google.com/drive/folders/1q1Pg9zox8rH5ztleHri2tuP41MexP2LA?usp=sharing)

<img src="fig/Study cities.png" width=900>

## File and data structure

<img src="fig/File and data structure.png" width=800>

The data directory contains two main folders – `access` and `ttm` (for TTMs).

### Accessibility values
The access folder contains 50 compressed comma-separated value (CSV) (.csv.gz) files corresponding to the largest urban areas shown in the map above. These files contain information of the zones of the three spatial administrative levels – county, census tract, and census block group (BG) – along with all the accessibility metrics.

> **Note**: In some cases, the number of rows may be slightly lesser than the sum of the number of zones mentioned in Table 1 across the three spatial levels due to unavailability of some data for accessibility computation. For instance, the file `access/las-vegas_bg.csv.gz` contains 1,784 rows which is slightly smaller than the 1,801 zones (1,276 BGs, 515 tracts, and 10 counties) of the Las Vegas–Henderson–Paradise, NV urban area (code 69184) whose principal city is Las Vegas.

Each data file contains 684 columns. The first nine columns contain general information of the zone. This includes the zone identifier `geoid`, given by the [FIPS](https://en.wikipedia.org/wiki/Federal_Information_Processing_Standards) code, a string of numbers with length 5, 11, and 12 for respectively counties, tracts, and BGs.
The other eight columns include the zone's spatial level, latitude and longitude of its centroid, name of its enclosing county, its population and size of labor force, and the total number of jobs and POIs.
The remaining columns denote the 675 accessibility metrics given in the general format of `{measure}_{kind}_{mode}_{threshold}`. These are explained in the following table. A complete list of these metric columns is provided in the helper file `access_metrics.csv`.

| Category | Code | Description/Formula |
| - | - | - |
| `{measure}` of accessibility | `Co` | Contour: Simply counts the total number of opportunities (also known as 'cumulative opportunities') |
| | `Gr` | Gravity measure: Weights opportunities by the time taken to reach them, given by 'impedance functions'. See [this paper](https://www.sciencedirect.com/science/article/pii/S0966692324002709) for info about impedance functions. |
| | `E2` | [Enhanced 2-Step Floating Catchment Area](https://www.sciencedirect.com/science/article/pii/S1353829209000574) |
| | `M2` | [Modified 2-Step Floating Catchment Area](https://doi.org/10.1016/j.healthplace.2013.07.012) |
| | `XM` | Cross-Modal Floating Catchment Area (XMFCA) | 
| `{kind}` of opportunity | `jobTot` | All jobs |
| | `jobWag` | Low-wage jobs |
| | `jobEdu` | Jobs for low-education workers |
| | `jobPOC` | Jobs for people of color |
| | `poiTot` | All POIs |
| | `poiEdu` | Educational facilities |
| | `poiGro` | Grocery shopping places |
| | `poiMed` | Medical amenities |
| | `poiSoc` | Social support facilities |
| `{mode}` of travel | `Dr` | Driving (car) |
| | `Bi` | Bicycling |
| | `Wa` | Walking |
| `{threshold}` of travel time | 15, 30, 45, 60, 90 | Threshold (upper bound) of travel time to be considered for accessibility: 15, 30, 45, 60, 90 min |

These metrics can be understood with some examples:
- The total number of grocery stores reachable (‘contour’ metric) by walking within 30 minutes is given by the field `Co_poiGro_Wa_30`.
- The number of jobs for people of color reachable with impedance decay (‘gravity’ metric) by driving within 60 minutes is given by `Gr_jobPOC_Dr_60`.
- Accessibility to medical facilities is usually measured by competition metrics because of competition for their limited capacity. Thus, it would be reasonable to use a metric like `M2_poiMed_Dr_30` to denote access to medical facilities by car within 30 minutes.
- When the purpose is to compare competition accessibility across modes, it is suitable to use the XMFCA metric. For example, to get the total accessibility to educational places by active transport (walking and bicycling), it is suitable to add the XMFCA access values: `XM_poiEdu_Wa_30` + `XM_poiEdu_Bi_30`.

## Usage
To use this code repository, it is best to create a [Conda](https://github.com/conda/conda) environment (named, for example, `saa`) and install the required dependencies after cloning this repository:

```
conda create -n saa python>=3.12

conda activate saa

pip install -r requirements.txt
```

## Description of source code files
| File | Description |
| --- | --- |
| [utils.py](utils.py) | Utility namespace for common packages, constants & helper functions used in the other files. |
| [get_ttm_osrm.py](get_ttm_osrm.py) | Script for collecting interzonal impedance using the [OSRM backend](https://github.com/Project-OSRM/osrm-backend) tool. |
| [get_ttm_r5.py](get_ttm_r5.py) | Script for collecting interzonal impedance using the [R5 routing engine](https://github.com/conveyal/r5) using the [`R5py`](https://r5py.readthedocs.io/en/stable/) library. |
| [extract_osm.sh](extract_osm.sh) | Extract the OpenStreetMap (OSM) geodatabase extract of the 50 largest urban areas using [`osmium-tool`](https://github.com/osmcode/osmium-tool). |
| [osrm_server.sh](osrm_server.sh) | Start a local OSRM routing server for the network of a given urban area for a given mode of travel. Needs [Docker](https://www.docker.com/) to work. |
| [1_Geometry.ipynb](1_Geometry.ipynb) | Prepare the geometry layer of the analysis zones for the US at different spatial scales using the [US Census Data API](https://www.census.gov/data/developers/guidance/api-user-guide.html) as well as [OpenStreetMap](https://www.openstreetmap.org) (OSM) database extracts for the MSAs. |
| [2_Opportunities.ipynb](2_Opportunities.ipynb) | Extract job counts and flows data from [LEHD LODES](https://lehd.ces.census.gov/data/). Also process Point of Interest (POI) location and visits data from SafeGraph Inc. |
| [3_Travel_times.ipynb](3_Travel_times.ipynb) | Extract and process travel time data using the [OSRM routing engine](https://github.com/Project-OSRM/osrm-backend). Also compute travel time matrices using the R5 and Google Distance Matrix API routing engines for technical validation. |
| [4_Compute_access.ipynb](4_Compute_access.ipynb) | Compute several measures of accessibility for the study regions using data prepared in the previous files. |
| [5_Compare_with_AAA.ipynb](5_Compare_with_AAA.ipynb) | Compare the SAA access values with the values obtained from the [Accessibility Across America (AAA)](https://www.cts.umn.edu/programs/ao) dataset. |
| [5_Scale_consistency.ipynb](5_Scale_consistency.ipynb) | Perform scale consistency check of accessibility data between (a) county vs tract and (b) tract vs BG levels. |