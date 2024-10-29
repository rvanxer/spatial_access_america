## Extract the OpenStreetMap (OSM) geodatabase extract of the 
## 50 largest urban areas of the US using the `osmium-tool`.
## To do this, a list of the largest cities, their bounding boxes, 
## and the associated US Census region was prepared in `geometry.ipynb`.
## For more details about osmium-tool, read its manual at:
## https://osmcode.org/osmium-tool/manual.html
{
    read # skip the first (header) line
    while read -r line; do
        # split the line into the variables of interest
        IFS=',' read -r city rgn minx miny maxx maxy <<< $line
        # if the regional extract doesn't exist, download it
        rgn_dir=data/osm/us_region
        mkdir -p $rgn_dir
        if [ ! -f $rgn_dir/$rgn.pbf ]; then
            echo "Downloading regional OSM database of US region: $rgn"
            fname=us-$rgn-latest.osm.pbf
            url=https://download.geofabrik.de/north-america/$fname
            wget $url # download in current directory
            mv $fname $rgn_dir/$rgn.pbf
        fi
        # if the city's extract doesn't exist, extract it using osmium-tool
        city_dir=data/osm/city
        mkdir -p $city_dir
        if [ ! -f $city_dir/$city.osm.pbf ]; then
            echo "Processing $city ($rgn)"
            bbox="$minx,$miny,$maxx,$maxy" # using the bounding box of the city
            time osmium extract -b $bbox $rgn_dir/$rgn.pbf -o $city_dir/$city.osm.pbf
        fi
done
} < data/city_region.csv
