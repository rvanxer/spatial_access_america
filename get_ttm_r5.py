"""
Obtain travel time matrices for different cities for a specific mode 
using the R5 routing engine. Note that it has a Java backend that needs
an OpenJDK version >=18 but also <22 (so do not install v22).
Use the following to set up a conda environment:
`conda create -n r5 --channel conda-forge r5py openjdk=21.0.1`

Use the script for a given mode as follows:
`python get_ttm_r5.py -M <mode> -c <cities>`
where <mode> is one of ['drive', 'walk', 'bike', 'transit']

R5 tutorial:
https://r5py.readthedocs.io/en/stable/user-guide/user-manual/travel-time-matrices.html
"""
#%%
import argparse

import r5py

from utils import *

#%%
def get_gtfs_files(city):
    city = city.lower().replace(' ', '-').replace('.', '')
    City = city.replace('-', ' ').title()
    city_bounds = gpd.read_parquet('data/geometry/city_bounds.parquet')
    feeds = gpd.read_parquet('data/gtfs/gtfs_feeds.parquet')
    feeds = feeds.sjoin(city_bounds.set_index('city').loc[[City]])
    files = [f'data/gtfs/all/{x}.zip' for x in feeds['mdb_id']]
    return files

#%%
def get_ttm(city, mode,
            departure=dt.datetime(2023, 11, 23, 8, 30),
            max_time=dt.timedelta(minutes=90),
            levels=('County', 'Tract', 'BG'), overwrite=False):
    now = dt.datetime.now
    assert mode in ['bike', 'drive', 'transit', 'walk'], mode
    print(t_start := now(), f'Started {city} by {mode}')
    city = city.lower().replace(' ', '-').replace('.', '')
    ts = departure.strftime('%Y%m%d-%H%M%S') # timestamp
    outpath = mkdir('data/ttm/r5') / f'{city}_{mode}_{ts}.parquet'
    if outpath.exists() and not overwrite:
        print('Skipping existing file:', outpath)
        return
    network = r5py.TransportNetwork(
        f'data/osm/city/{city}.osm.pbf',
        get_gtfs_files(city) if mode == 'transit' else [])
        # glob(f'data/gtfs/all/*.zip') if mode == 'transit' else [])
    print(now(), 'Prepared network:', (t := now()) - t_start)
    ttm = [] # output travel time matrix
    centroids = pd.read_parquet('data/geometry/centroids.parquet')
    for level in levels:
        pts = filt(centroids, city=city, level=level.lower())
        pts = pdf2gdf(pts, 'x', 'y', CRS_DEG)
        pts = pts.rename(columns=D(geoid='id'))[['id', 'geometry']]
        computer = r5py.TravelTimeMatrixComputer(
            network, origins=pts, destinations=pts,
            departure=departure, transport_modes={
                'drive':   [r5py.TransportMode.CAR],
                'bike' :   [r5py.TransportMode.BICYCLE],
                'walk' :   [r5py.TransportMode.WALK],
                'transit': [r5py.TransportMode.TRANSIT,
                            r5py.TransportMode.WALK]
            }[mode], max_time=max_time)
        times = computer.compute_travel_times().dropna()
        ttm.append(times.assign(level=level))
        print(now(), f'Routed for {level}:', -(t - (t := now())))
    ttm = (pd.concat(ttm).reset_index(drop=1)
           .rename(columns=D(from_id='src', to_id='trg', travel_time='time'))
           .astype(D(level=CAT, src=CAT, trg=CAT, time=I16))
           [['level', 'src', 'trg', 'time']])
    ttm.to_parquet(outpath, compression='gzip')
    print(t := now(), f'Ended {city} by {mode}; Runtime: {t - t_start}')
    return ttm

#%%
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # travel mode of interest (one of {bike, drive, transit, walk})
    parser.add_argument('-M', '--mode')
    # list of cities (lowercase, hyphenated names), separated by ','
    parser.add_argument('-c', '--cities')
    # whether overwrite the existing file
    parser.add_argument('-o', '--overwrite', action='store_true')
    parser.set_defaults(overwrite=False)
    kw = parser.parse_args()
    mode = kw.mode.lower()
    for city in kw.cities.split(','):
        try:
            get_ttm(city, mode, overwrite=kw.overwrite)
        except Exception as e:
            print(f'ERROR in {city} by {mode}:', e)

#%%
