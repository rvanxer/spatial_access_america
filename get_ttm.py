#%% Imports
import argparse
import requests

from utils import *

#%% Main routine
def get_ttm(city, mode, level, ip, batch_size=3000, max_time=90 * 60):
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
        Maximum travel time (in seconds) in the resulting table, used to
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
    tstart = dt.datetime.now()
    mode_label = 'driving' if mode == 'drive' else mode
    pts = pd.read_parquet('data/centroids.parquet')
    pts = filt(pts, city=city, level=level)
    if len(pts) <= 1:
        return
    xy = ';'.join([f'{x:.6f},{y:.6f}' for x, y in zip(pts.x, pts.y)])
    batches = list(np.arange(0, len(pts), batch_size)) + [len(pts)]
    combs = np.split(np.arange(0, len(pts)), batches)[1:-1]
    od = []
    for ix, iy in tqdm(it.product(*[combs] * 2), total=len(combs) ** 2):
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
        dur = (Pdf(data['durations'], index=ix, columns=iy)
               .reset_index().melt('index', value_name='time'))
        df = pd.concat([dist, dur['time']], axis=1)
        df = df.query(f'0 <= time <= {max_time}')
        df = df.astype(D(src_i=I32, trg_i=I32, dist=F32, time=F32))
        od.append(df)
    od = pd.concat(od).reset_index(drop=1)
    od = od.merge(pts.geoid.rename('src'), left_on='src_i', right_index=True)
    od = od.merge(pts.geoid.rename('trg'), left_on='trg_i', right_index=True)
    od = od.astype(D(src=CAT, trg=CAT))[['src', 'trg', 'dist', 'time']]
    outfile = mkdir(f'data/ttm/{city}') / f'{city}_{mode}_{level}.parquet'
    od.to_parquet(outfile, compression='gzip')
    tend = dt.datetime.now()
    print(f'{tend}: Runtime for {city}/{mode}/{level}: {tend - tstart}')
    return od

#%% Script run
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('-c', '--city') # name of target city
    arg('-m', '--mode') # travel mode
    arg('-l', '--levels', default='county-tract-bg') # spatial level(s)
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
