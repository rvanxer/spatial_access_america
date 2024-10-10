#! /bin/zsh
## This script starts a local OSRM routing server for the network of a given US 
## urban area for a given mode of travel. The docker engine must be running 
## before this. See the OSRM backend doc for details: 
## https://github.com/Project-OSRM/osrm-backend.
## 
## Once the server starts, the Python script 'osrm.py' is to be used to compute 
## the OD matrix and write in parquet files.
## 
## Example: 'zsh osrm.sh 12060-atlanta drive'
## 
## Parameters:
## - 'city': (Required) ID of the region, given by the syntax
##     '{FIPS code}-{friendly-name}'.
##     The friendly name must be the same as the one for which OSM file 
##     exists on the GeoFabrik server. For example, '35620-new-york' indicates
##     the New York City metro area whose FIPS code is 35620.
## 
## - 'mode': (Required) Mode of travel. The server initialization requires setting
##     up routing for a specific profile specified by its mode of travel.
##     Currently, OSRM backend by default supports 3 profiles corresponding to the
##     modes 'drive', 'bike', 'walk'.
## 
## - 'port': (Optional, default 5108) Port number on which the local server will
##     listen.
## 
## - 'nmax': (Optional, default 3000) Maximum no. of rows in the OD table that the
##     server can process in one iteration. Depending on the host's RAM, this 
##     number may be increased for faster processing.
# *********************************************************
# resolve the parameters and assign default values, if any
city=$1
mode=$2
port=${3:-5108} # server port number
nmax=${4:-3000} # maximum batch size
# make sure the mode is acceptable
# source: https://stackoverflow.com/a/15394738/5711244
declare -a modes=(bike drive walk)
if [[ ! " ${modes[*]} " =~ " ${mode} " ]]; then
    echo "Invalid mode: $mode"
    exit 1
fi
echo "-----\nPROCESSING '$city' by '$mode' on port $port"
# mount the OSM data directory for the given region to the docker image
data_dir="$PWD/data/osrm/$city:/data"
# resolve the compressed OSM database file (PBF format) in docker
pbf_file=/data/$city.osm.pbf
# base URL for the OSRM backend
url="ghcr.io/project-osrm/osrm-backend"
# create associative array for modal routing profiles
declare -A prof # profile name for each mode
prof[drive]="car"; prof[walk]="foot"; prof[bike]="bicycle"
# extract the database and initialize it with the given mode's profile
profile=${prof[$mode]}
prof_file="/opt/$profile.lua"
echo "Extracting the graph with '$profile' profile"
sudo docker run -t -v $data_dir $url osrm-extract -p $prof_file $pbf_file > /dev/null
# get the processed OSRM database file
osrm_file=/data/$city.osrm
# create partitions
echo "Partitioning the graph"
sudo docker run -t -v $data_dir $url osrm-partition $osrm_file > /dev/null
# customize the backend
echo "Customizing the backend"
sudo docker run -t -v $data_dir $url osrm-customize $osrm_file > /dev/null
# run the server
echo "Setting up routing server on http://0.0.0.0:$port"
sudo docker run -p $port:$port -v $data_dir $url osrm-routed \
--port $port --max-table-size $nmax --algorithm mld $osrm_file
# compute the distances & travel times
# python get_ttm.py -c $city -m $mode -p $port
