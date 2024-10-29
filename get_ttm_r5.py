"""
Obtain travel time matrices for different cities for a specific mode 
using the R5 routing engine. Note that it has a Java backend that needs
an OpenJDK version >=18 but also <22 (so do not install v22).
Use the following to set up a conda environment:
`conda create -n r5 --channel conda-forge r5py openjdk=21.0.1`

Use the script for a given mode as follows:
`python get_ttm_r5.py -M <mode>`
where <mode> is one of ['drive', 'walk', 'bike', 'transit']

R5 tutorial:
https://r5py.readthedocs.io/en/stable/user-guide/user-manual/travel-time-matrices.html
"""
#%%
import argparse

import r5py

from utils import *

#%%
def get_ttm(city, mode,
            departure=dt.datetime(2023, 11, 23, 8, 30),
            levels=('County', 'Tract', 'BG'), overwrite=False):
    assert mode in ['bike', 'drive', 'transit', 'walk'], mode
    print(started := dt.datetime.now(), f'Started {city} by {mode}')
    city = city.lower().replace(' ', '-').replace('.', '')
    ts = departure.strftime('%Y%m%d-%H%M%S') # timestamp
    outpath = mkdir('data/ttm/r5') / f'{city}_{mode}_{ts}.parquet'
    if outpath.exists() and not overwrite:
        print('Skipping existing file:', outpath)
        return
    network = r5py.TransportNetwork(
        f'data/osm/city/{city}.pbf',
        glob(f'data/gtfs/{city}/*.zip') if mode == 'transit' else [])
    ttm = [] # output travel time matrix
    centroids = pd.read_parquet('data/centroids.parquet')
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
            }[mode])
        times = computer.compute_travel_times().dropna()
        ttm.append(times.assign(level=level))
    ttm = (pd.concat(ttm).reset_index(drop=1)
           .rename(columns=D(from_id='src', to_id='trg',
                             travel_time='time'))
           [['level', 'src', 'trg', 'time']]
           .astype(D(level=CAT, src=CAT, trg=CAT, time=I16)))
    ttm.to_parquet(outpath, compression='gzip')
    print(ended := dt.datetime.now(),
          f'Ended {city} by {mode}; Runtime: {ended - started}')
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
