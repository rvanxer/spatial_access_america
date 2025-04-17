#%% [markdown]
#%%
import dash
from dash import dcc, Input, Output
from dash.html import Div, Label
import geopandas as gpd
import pandas as pd
import plotly.express as px

#%% Parameters
cities = {x: x for x in [
    'Austin',
    'Boston',
    'Chicago',
    'Indianapolis',
    'Miami',
    'Minneapolis',
    'Pittsburgh',
    'Raleigh',
    'Seattle',
    'Washington',
]}
measures = {x: x for x in [
    'Contour',
    'Gravity',
    'E2SFCA',
    'M2SFCA',
]}
thresholds = {f'{t} min': f'{t} min' for t in [30, 15, 60]}
levels = {
    'Tract': 'Census tract',
    'BG': 'Census block group',
    'County': 'County',
}
kinds = {
    'Jobs: All': 'Total jobs',
    'Jobs: Low wage': 'Jobs for low-wage workers',
    'POIs: All': 'Total points of interest (POIs)',
    'POIs: Medical': 'Medical amenities',
    'POIs: Social Support': 'Social support facilities',
    'EVCI: Stations': 'Electric vehicle charging stations',
}
modes = {
    'Drive': 'Driving (auto)',
    'Bike': 'Bicycling',
    'Walk': 'Walking',
}

#%%
metrics = pd.read_csv('access_metrics.csv')
metrics = metrics[metrics.kind.isin(kinds)]
metrics = metrics[metrics['mode'].isin(modes)]
metrics = metrics[metrics.thresh.isin(thresholds)]

#%%
# access = []
# for city in cities:
#     city_ = city.lower().replace(' ', '-').replace('.', '')
#     zones = gpd.read_parquet('data/geometry/zones.parquet',
#                              filters=[('city', '==', city)],
#                              columns='geoid geometry level city'.split())
#     xs = pd.read_csv(f'data/export/access/{city_}.csv.gz',
#                      usecols=['geoid'] + list(metrics.field))
#     xs = xs.astype(D(geoid=str) | {c: F32 for c in xs.select_dtypes(F64).columns})
#     access.append(zones.merge(xs))
# access = (pd.concat(access).reset_index(drop=1)
#           .astype(D(city=CAT, level=CAT)))
# access.to_parquet('dashboard_data.parquet', compression='gzip')
access = gpd.read_parquet('dashboard_data.parquet')

#%%
filter_divs = [Label('Filters:')]
for col, label, options in [
    ('city', 'Urban area', cities),
    ('level', 'Spatial level', levels),
    ('measure', 'Access measure', measures),
    ('kind', 'Opportunity type', kinds),
    ('mode', 'Travel mode', modes),
    ('thresh', 'Travel time threshold', thresholds),
]:
    filter_divs.append(Div([
        Label(label + ':', className='dropdown-label'),
        dcc.Dropdown(id=f'{col}-dropdown', className='dropdown-menu',
                     options=[dict(value=k, label=v) for k, v in options.items()],
                     value=list(options.keys())[0])
        ], className='container'))
sidebar = Div(filter_divs, id='sidebar')

#%%
map_container = Div([
    dcc.Graph(id='map')
], id='map-container')

#%%
app = dash.Dash(__name__, external_stylesheets=['dashboard.css'])

app.layout = Div([
    sidebar,
    map_container,
], id='main-container')

@app.callback(
    Output('map', 'figure'),
    [Input(x + '-dropdown', 'value') for x in
     'city level measure kind mode thresh'.split()]
)
def update_map(city, level, measure, kind, mode, thresh):
    metric = metrics.query(' & '.join([
        f'measure == "{measure}"',
        f'kind == "{kind}"',
        f'mode == "{mode}"',
        f'thresh == "{thresh}"'
    ]))['field'].iloc[0]
    xs = access.query(f'city == "{city}" & level == "{level}"')
    xs = xs.drop(columns=['city', 'level']).set_index('geoid')
    box = xs.bounds.apply(dict(minx=min, miny=min, maxx=max, maxy=max))
    cx, cy = (box.minx + box.maxx) / 2, (box.miny + box.maxy) / 2
    fig = px.choropleth_mapbox(
        xs, geojson=xs.geometry.__geo_interface__,
        locations=xs.index, color=metric, labels={metric: 'Access value'},
        title=f'Accessibility distribution for `{metric}`', opacity=0.7)
    fig.update_layout(
        height=1000,
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(len=0.8, lenmode='fraction', x=0.5, y=1.02,
                                orientation='h', xanchor='center', yanchor='bottom'),
        mapbox=dict(style='open-street-map', zoom=9, center=dict(lon=cx, lat=cy)),
        font=dict(family='Arial', size=16),
    )
    return fig

#%% Run app
if __name__ == '__main__':
    app.run(debug=True)

#%%