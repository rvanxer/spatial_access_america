## Extract the OpenStreetMap (OSM) geodatabase extract of the 
## 50 largest urban areas of the US using the `osmium-tool`.
## To do this, a list of the largest cities, their bounding boxes, 
## and the associated US Census region was prepared in `geometry.ipynb`.
## Reference: https://osmcode.org/osmium-tool/manual.html
while read -r line; do
    # split the line into the variables of interest
    IFS=',' read -r city rgn minx miny maxx maxy <<< $line
    # if the regional extract doesn't exist, download it
    rgn_dir=data/osm/region
    mkdir -p $rgn_dir
    if [ ! -f $rgn_dir/$rgn.pbf ]; then
        fname=us-$rgn-latest.osm.pbf
        url=https://download.geofabrik.de/north-america/$fname
        wget -p $rgn_dir $url
        mv $rgn_dir/$fname $rgn_dir/$rgn.pbf
    fi
    # if the city's extract doesn't exist, extract it using osmium-tool
    city_dir=data/osm/city
    mkdir -p $city_dir
    if [ ! -f $city_dir/$city.pbf ]; then
        echo "Processing $city ($rgn)"
        bbox="$minx,$miny,$maxx,$maxy" # using the bounding box of the city
        time osmium extract -b $bbox $rgn_dir/$rgn.pbf -o $city_dir/$city.pbf
    fi
done < data/city_region.csv
