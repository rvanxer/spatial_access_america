#%% Imports
# Commonly used built-in imports
import datetime as dt
from functools import reduce
from glob import glob
import itertools as it
import os, sys
import re
from pathlib import Path
import warnings

# Commonly used external imports
import contextily as ctx
from IPython.display import display
import geopandas as gpd
from geopandas import GeoDataFrame as Gdf
from geopandas import GeoSeries
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import numpy as np
from numpy import array as Arr
import pandas as pd
from pandas import DataFrame as Pdf
from pandas import Series
# from pyarrow.parquet import read_schema
import seaborn as sns
from tqdm.notebook import tqdm

#%% Aliases of classes and data types
D = dict # Python dictionary
CAT = 'category'
I8, I16, I32, I64 = np.int8, np.int16, np.int32, np.int64
F16, F32, F64 = np.float16, np.float32, np.float64

#%% Other important constants
CRS_DEG = 'EPSG:4326' # geographical CRS (unit: degree)
CRS_M = 'EPSG:3857' # spatial CRS (unit: meter)

#%% Unit conversion factors
M2FT = 3.28084 # meter to feet
FT2M = 1 / M2FT
MI2M = 1609.34  # mile to meter
M2MI = 1 / MI2M
MI2KM = 1.60934  # mile to kilometer
KM2MI = 1 / MI2KM
SQMI2SQM = 2.59e6  # sq. mile to sq. meter
SQM2SQMI = 1 / SQMI2SQM # sq. m. to sq. mi.
MPS2MPH = 2.2369363 # meters per second to miles per hr
MPH2MPS = 1 / MPS2MPH # miles per hr to meters per second

#%% Default plot settings
plt.rcParams.update({
    'axes.edgecolor': 'k',
    'axes.edgecolor': 'k',
    'axes.formatter.use_mathtext': True,
    'axes.grid': True,
    'axes.labelcolor': 'k',
    'axes.labelsize': 13,
    'axes.linewidth': 0.5,
    'axes.titlesize': 15,
    'figure.dpi': 150,
    'figure.titlesize': 15,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Noto Sans', 'DejaVu Serif'],
    'grid.alpha': 0.15,
    'grid.color': 'k',
    'grid.linewidth': 0.5,
    'legend.edgecolor': 'none',
    'legend.facecolor': '.9',
    'legend.fontsize': 11,
    'legend.framealpha': 0.5,
    'legend.labelcolor': 'k',
    'legend.title_fontsize': 13,
    'mathtext.fontset': 'cm',
    'text.color': 'k',
    'text.color': 'k',
    'xtick.bottom': True,
    'xtick.color': 'k',
    'xtick.labelsize': 10,
    'xtick.minor.visible': True,
    'ytick.color': 'k',
    'ytick.labelsize': 10,
    'ytick.left': True,
    'ytick.minor.visible': True,
})

def mkdir(path):
    """Shorthand for making a folder if it does not exist."""
    assert isinstance(path, str) or isinstance(path, Path)
    Path(path).mkdir(exist_ok=True, parents=True)
    return Path(path)


def factor(x):
    """Create a categorical series with categories in the original order."""
    cats = pd.Series(x).drop_duplicates()
    return pd.Categorical(x, categories=cats)


def normalize(x, vmin=None, vmax=None):
    """Normalize an array of values to fit in the range [0, 1]."""
    if isinstance(x, list) or isinstance(x, tuple):
        x = np.array(x)
    vmin = vmin or np.min(x)
    vmax = vmax or np.max(x)
    return (x - vmin) / (vmax - vmin)


def filt(df: Pdf, reset: bool = True, **kwargs) -> Pdf:
    """Filter a dataframe with keyword arguments."""
    masks = [(df[k] == v) for k, v in kwargs.items()]
    mask = reduce(pd.Series.mul, masks, pd.Series(True, df.index))
    df = df[mask].drop(columns=list(kwargs), errors='ignore')
    if reset:
        df = df.reset_index(drop=True)
    return df


def pdf2gdf(df: Pdf, x: str = 'lon', y: str = 'lat', crs=None) -> Gdf:
    """Convert a pandas DataFrame to a geopandas GeoDataFrame by creating 
    point geometry from the dataframes x & y columns."""
    geom = gpd.points_from_xy(df[x], df[y], crs=crs)
    return gpd.GeoDataFrame(df, geometry=geom)


def plot(ax=None, fig=None, size=None, dpi=None, title=None, xlab=None,
         ylab=None, xlim=None, ylim=None, titlesize=None, xlabsize=None,
         ylabsize=None, xeng=False, yeng=False, xticks=None, yticks=None,
         xangle=None, yangle=None, xlog=False, ylog=False,
         xminor=True, yminor=True, axoff=False, gridcolor=None,
         bordercolor=None) -> plt.Axes:
    """Custom handler for matplotlib plotting options."""
    if isinstance(size, tuple) and fig is None:
        fig, ax = plt.subplots(figsize=size, dpi=dpi)
    ax = ax or plt.gca()
    ax.set_title(title, fontsize=titlesize or mpl.rcParams['axes.titlesize'])
    ax.set_xlabel(xlab, fontsize=xlabsize or mpl.rcParams['axes.labelsize'])
    ax.set_ylabel(ylab, fontsize=ylabsize or mpl.rcParams['axes.labelsize'])
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    if xeng: ax.xaxis.set_major_formatter(mpl.ticker.EngFormatter())
    if yeng: ax.yaxis.set_major_formatter(mpl.ticker.EngFormatter())
    if xlog: ax.set_xscale('log')
    if ylog: ax.set_yscale('log')
    if xticks: ax.set_xticks(xticks)
    if yticks: ax.set_yticks(yticks)
    if xangle: ax.set_xticklabels(ax.get_xticklabels(), rotation=xangle)
    if yangle: ax.set_yticklabels(ax.get_yticklabels(), rotation=yangle)
    if xminor: ax.tick_params(which='minor', bottom=True)
    else: ax.tick_params(which='minor', bottom=False)
    if yminor: ax.tick_params(which='minor', left=True)
    else: ax.tick_params(which='minor', left=False)
    if axoff: ax.axis('off')
    if gridcolor: ax.grid(color=gridcolor)
    if bordercolor:
        for s in ['left', 'right', 'top', 'bottom']:
            ax.spines[s].set_color(bordercolor)
    fig = fig or plt.gcf()
    return ax


def basemap(ax: plt.Axes, source='CartoDB.Voyager', crs=None,
            scale=0.2, scale_kw={}, ticks=False, **kwargs):
    bunch, provider = source.split('.')
    ctx.add_basemap(ax=ax, source=ctx.providers[bunch][provider],
                    crs=crs, **kwargs)
    if scale is not None:
        ax.add_artist(ScaleBar(scale, **scale_kw))
    if not ticks:
        ax.set_xticks([])
        ax.set_yticks([])
    return ax


def maplot(df: gpd.GeoDataFrame, col=None, ax=None, size=(6, 6),
           dpi=150, title=None, legend=True, cmap='rainbow',
           vmin=None, vmax=None, shrink=0.5, label=None,
           vert=True, cbar_kw={}, bgmap=True, bgmap_kw={},
           **kwargs) -> plt.Axes:
    """Custom map plot for geopandas dataframes."""
    ax = ax or plot(size=size, dpi=dpi, title=title)
    kwds = dict(orientation='vertical' if vert else 'horizontal',
                shrink=shrink, label=label) | cbar_kw
    df.plot(col, ax=ax, vmin=vmin, vmax=vmax, cmap=cmap,
            legend=legend, legend_kwds=kwds, **kwargs)
    if bgmap:
        ax = basemap(ax, crs=df.crs, **bgmap_kw)
    return ax


def imsave(title=None, fig=None, ax=None, dpi=300,
           root='./fig', ext='png', opaque=True):
    """Save the current matplotlib figure to disk."""
    fig = fig or plt.gcf()
    ax = ax or fig.axes[0]
    title = title or fig._suptitle or ax.get_title() or 'Untitled {}'.format(
        dt.datetime.now().strftime('%Y-%m-%d_%H-%m-%S'))
    title = re.sub(r'[^A-Za-z\s\d,.-]', '_', title)
    fig.savefig(f'{mkdir(root)}/{title}.{ext}', dpi=dpi, bbox_inches='tight',
                transparent=not opaque, facecolor='white' if opaque else 'auto')


def view(x: Pdf | Series | Gdf | GeoSeries, top: int = 1, mem=True):
    """Custom display for pandas and geopandas dataframe and series objects 
    in Jupyter. This is a combination of methods like `head`, `dtypes`, and
    `memory_usage`."""
    def f(tabular: bool, crs: bool, mem=mem):
        """
        tabular : Is the object `x` a 2D (matrix or table-like) structure?
        crs : Does the object `x` have a CRS, i.e., is it geographic/geometric?
        """
        shape = ('{:,} rows x {:,} cols'.format(*x.shape) if tabular
                 else f'{x.size:,} rows')
        mem = x.memory_usage(deep=True) / (1024 ** 2) if mem else None
        memory = f'Memory: {(mem.sum() if tabular else mem):.1f} MiB'
        crs = repr(x.crs).split('\n')[0] if crs else ''
        print(shape + '; ' + memory + ('; ' + crs if crs else ''))
        if tabular:
            types = {x.index.name or '': '<' + x.dtypes.astype(str) + '>'}
            types = pd.DataFrame(types).T
            display(pd.concat([types, x.head(top).astype({'geometry': str}) 
                               if crs else x.head(top)]))
        else:
            print(x.head(top))

    if isinstance(x, gpd.GeoDataFrame):
        f(True, True)
    elif isinstance(x, pd.DataFrame):
        f(True, False)
    elif isinstance(x, gpd.GeoSeries):
        f(False, True)
    elif isinstance(x, pd.Series):
        f(False, False)
    return x
