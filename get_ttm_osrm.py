#%% Imports
import argparse
import requests

from utils import *

#%% Main routine
def get_ttm(city, mode, level, ip, batch_size=3000,
            max_time=90, overwrite=False):
    """Compute the all-to-all distance/travel time OD matrix for all the zones
    of the given combination of city, mode, and spatial level.

    Parameters
    ----------
    city : str
        Name of the target city (should be in same format as is the OSM file).
    mode : str in ['bike', 'drive', 'walk']
        Travel mode.
    level : str in ['bg', 'county', 'tract']
        Spatial level of zones.
    ip : str
        IP address of the local OSRM server along with the port number.
    batch_size : int, optional
        Maximum batch size of the OSRM server, used to partition the zones.
    max_time : float, optional
        Maximum travel time (in minutes) in the resulting table, used to
        reduce the file size of the output table.

    Returns
    -------
    pandas.DataFrame
        Travel time matrix in the long form with the following columns:
        - src, trg: FIPS codes of the origin (src) & destination (trg) zones.
        - dist: Length of the time-shortest route (meters).
        - time: Duration of the time-shortest route (seconds).
    """
    assert mode in ['bike', 'drive', 'walk'], mode
    assert level in ['bg', 'county', 'tract'], level
    outpath = mkdir(f'data/ttm/osrm') / f'{city}_{mode}_{level}.parquet'
    if outpath.exists() and not overwrite:
        print('Skipping existing file:', outpath)
        return
    tstart = dt.datetime.now()
    mode_label = 'driving' if mode == 'drive' else mode
    pts = pd.read_parquet('data/geometry/centroids.parquet')
    pts = filt(pts, city=city, level=level)
    if len(pts) <= 1:
        return
    xy = ';'.join([f'{x:.6f},{y:.6f}' for x, y in zip(pts.x, pts.y)])
    batches = list(np.arange(0, len(pts), batch_size)) + [len(pts)]
    combs = np.split(np.arange(0, len(pts)), batches)[1:-1]
    ttm = [] # output travel time matrix
    for ix, iy in it.product(*[combs] * 2):
        src = 'sources=' + ';'.join(ix.astype(str))
        trg = 'destinations=' + ';'.join(iy.astype(str))
        annot = 'annotations=distance,duration'
        url = f'{ip}/table/v1/{mode_label}/{xy}?{annot}'
        if len(combs) > 1:
            url += f'&{src}&{trg}'
        data = requests.get(url).json()
        dist = (Pdf(data['distances'], index=ix, columns=iy)
                .rename_axis('src_i').reset_index()
                .melt('src_i', var_name='trg_i', value_name='dist'))
        dur = (Pdf(Arr(data['durations']) / 60, index=ix, columns=iy)
               .reset_index().melt('index', value_name='time'))
        df = pd.concat([dist, dur['time']], axis=1)
        df = df.query(f'0 <= time <= {max_time}')
        df = df.astype(D(src_i=I32, trg_i=I32, dist=F32, time=F32))
        ttm.append(df)
    ttm = (pd.concat(ttm).reset_index(drop=1)
           .merge(pts.geoid.rename('src'), left_on='src_i', right_index=True)
           .merge(pts.geoid.rename('trg'), left_on='trg_i', right_index=True)
           .astype(D(src=CAT, trg=CAT)).reset_index(drop=True)
           [['src', 'trg', 'dist', 'time']])
    ttm.to_parquet(outpath, compression='gzip')
    tend = dt.datetime.now()
    print(f'{tend}: Runtime for {city}/{mode}/{level}: {tend - tstart}')
    return ttm

#%% Script run
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('-c', '--city') # name of target city
    arg('-m', '--mode') # travel mode
    arg('-l', '--levels', default='county-tract-bg') # spatial level(s)
    arg('-o', '--overwrite', action='store_true')
    parser.set_defaults(overwrite=False)
    arg('-p', '--port', type=int, default=5108) # port number
    kw = parser.parse_args() # keyword arguments
    ip = f'http://0.0.0.0:{kw.port}' # IP address of server
    for level in kw.levels.split('-'):
        print(label := f'{kw.city}/{kw.mode}/{level}')
        try:
            get_ttm(kw.city, kw.mode, level, ip=ip)
        except Exception as e:
            print('ERROR:', label, e)

#%%
