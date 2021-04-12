# DUG-seis visualization
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import os
from sys import platform
import glob

import flask
import numpy as np
import pandas as pd

import dash
import dash_table
from dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
static_image_route = '/static/'


def event_table(df, derived_virtual_selected_rows=None):
    if derived_virtual_selected_rows is None:
        derived_virtual_selected_rows = list(range(len(df.index)))
    return dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {'id': 'Id', 'name': 'Id'},
            {'id': 'Date & Time', 'name': 'Date & Time'},
            {'id': 'x', 'name': 'x', 'format': Format(precision=3, scheme=Scheme.fixed)},
            {'id': 'y', 'name': 'y', 'format': Format(precision=3, scheme=Scheme.fixed)},
            {'id': 'z', 'name': 'z', 'format': Format(precision=3, scheme=Scheme.fixed)},
            {'id': 'Mag', 'name': 'Mag', 'format': Format(precision=1, scheme=Scheme.fixed)},
            {'id': 'loc_rms', 'name': 'loc_rms', 'format': Format(precision=2, scheme=Scheme.fixed)},
            {'id': 'npicks', 'name': 'npicks'}],
        n_fixed_rows=1,
        data=df.to_dict('rows'),
        style_table={
            'maxHeight': '300',
            'overflowY': 'scroll',
            'overflowX': 'scroll',
        },
        style_header={
            # 'backgroundColor': 'white',
            'fontWeight': 'bold',
        },
        style_cell={'textAlign': 'center',
                    'whiteSpace': 'no-wrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                    },
        editable=False,
        filtering=True,
        sorting=True,
        sorting_type='single',
        row_selectable='multi',
        selected_rows=derived_virtual_selected_rows,
    )


def call_event_table():
    if os.path.isfile('events.csv'):
        df = pd.read_csv('events.csv', header=None,
                         names=['Id', 'Date & Time', 'x', 'y', 'z', 'Mag', 'loc_rms', 'npicks'])
        #df['Date & Time'] = pd.to_datetime(df['Date & Time'])
        #df.round(pd.Series([1, 0, 2], index=['Mag', 'y', 'z']))
        return html.Div(children=event_table(df), id='table-container')


def serve_layout():
    event_image_directory = os.getcwd() + '/event_figs_passive/'
    list_of_event_images = sorted([os.path.basename(x) for x in glob.glob('{}*.png'.format(event_image_directory))])
    if len(list_of_event_images) == 0:
        list_of_event_images.append('')
    noise_image_directory = os.getcwd() + '/noise_vis/'
    list_of_noise_images = sorted([os.path.basename(x) for x in glob.glob('{}*.png'.format(noise_image_directory))])
    if len(list_of_noise_images) == 0:
        list_of_noise_images.append('')

    return html.Div(children=[
        html.H1('DUG-Seis Dashboard'),
        html.H4('Choose update time for event list:'),
        dcc.RadioItems(id='set-time',
                       value=5000,
                       options=[
                           {'label': 'Every second', 'value': 1000},
                           {'label': 'Every 5 seconds', 'value': 5000},
                           {'label': 'Every 30 seconds', 'value': 30000},
                           {'label': 'Off', 'value': 1000000000}
                       ]),
        html.P('On update, the selected events are kept, but sorting, filtering and figure view is reset.'),
        html.H4('Event List:'),
        call_event_table(),
        html.Div(id='datatable-interactivity-container'),
        html.H4('Event Waveforms:'),
        dcc.Dropdown(
            id='event-image-dropdown',
            options=[{'label': i, 'value': i} for i in list_of_event_images],
            value=list_of_event_images[-1]
        ),
        html.Img(id='event-image', style={'width': '100%'}),
        html.H4('Noise:'),
        dcc.Dropdown(
            id='noise-image-dropdown',
            options=[{'label': i, 'value': i} for i in list_of_noise_images],
            value=list_of_noise_images[-1]
        ),
        html.Img(id='noise-image', style={'width': '100%'}),
        dcc.Interval(
            id='interval-component',
            interval=5 * 1000,  # in milliseconds
            n_intervals=0
        ),

    ])


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
app.layout = serve_layout


@app.server.route('{}<image_path>.png'.format(static_image_route))
def serve_image(image_path):
    if 'event' in image_path:
        image_directory = os.getcwd() + '/event_figs_passive/'
    elif 'noise' in image_path:
        image_directory = os.getcwd() + '/noise_vis/'
    list_of_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(image_directory))]
    image_name = '{}.png'.format(image_path)
    if image_name not in list_of_images:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    return flask.send_from_directory(image_directory, image_name)


@app.callback(
    dash.dependencies.Output('event-image', 'src'),
    [dash.dependencies.Input('event-image-dropdown', 'value')])
def update_image_src(value):
    return static_image_route + value

@app.callback(
    dash.dependencies.Output('noise-image', 'src'),
    [dash.dependencies.Input('noise-image-dropdown', 'value')])
def update_image_src(value):
    return static_image_route + value


@app.callback(
    dash.dependencies.Output('interval-component', 'interval'),
    [dash.dependencies.Input('set-time', 'value')])
def update_interval(value):
    return value


@app.callback(Output('table-container', 'children'),
              [Input('interval-component', 'n_intervals')],
              [State('datatable-interactivity', 'derived_virtual_data'),
               State('datatable-interactivity', 'derived_virtual_selected_rows')])
def update_table(n, rows, derived_virtual_selected_rows):
    if derived_virtual_selected_rows is None:
        derived_virtual_selected_rows = []

    df = pd.read_csv('events.csv', header=None,
                     names=['Id', 'Date & Time', 'x', 'y', 'z', 'Mag', 'loc_rms', 'npicks'])
    df['Date & Time'] = pd.to_datetime(df['Date & Time'])

    dff = pd.DataFrame(rows)
    if len(dff.index) < len(df.index):
        [derived_virtual_selected_rows.append(i) for i in range(len(dff.index), len(df.index))]
    return event_table(df, derived_virtual_selected_rows)


@app.callback([Output('event-image-dropdown', 'options'),
               Output('noise-image-dropdown', 'options'),
               Output('event-image-dropdown', 'value'),
               Output('noise-image-dropdown', 'value')],
              [Input('interval-component', 'n_intervals')])
def update_dropdowns(n):
    event_image_directory = os.getcwd() + '/event_figs_passive/'
    list_of_event_images = sorted([os.path.basename(x) for x in glob.glob('{}*.png'.format(event_image_directory))])
    if len(list_of_event_images) == 0:
        list_of_event_images.append('')
    event_options = [{'label': i, 'value': i} for i in list_of_event_images]
    noise_image_directory = os.getcwd() + '/noise_vis/'
    list_of_noise_images = sorted([os.path.basename(x) for x in glob.glob('{}*.png'.format(noise_image_directory))])
    if len(list_of_noise_images) == 0:
        list_of_noise_images.append('')
    noise_options = [{'label': i, 'value': i} for i in list_of_noise_images]

    return event_options, noise_options, list_of_event_images[-1], list_of_noise_images[-1]


@app.callback(Output('datatable-interactivity-container', 'children'),
    [Input('datatable-interactivity', 'derived_virtual_data'),
    Input('datatable-interactivity', 'derived_virtual_selected_rows')])
def update_graph(rows, derived_virtual_selected_rows):
    # When the table is first rendered, `derived_virtual_data` and
    # `derived_virtual_selected_rows` will be `None`. This is due to an
    # idiosyncracy in Dash (unsupplied properties are always None and Dash
    # calls the dependent callbacks when the component is first rendered).
    # So, if `rows` is `None`, then the component was just rendered
    # and its value will be the same as the component's dataframe.
    # Instead of setting `None` in here, you could also set
    # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # the component.
    if derived_virtual_selected_rows is None:
        derived_virtual_selected_rows = []

    df = pd.read_csv('events.csv', header=None,
                     names=['Event_id', 'Date & Time', 'x', 'y', 'z', 'Mag', 'loc_rms', 'npicks'])
    df['Date & Time'] = pd.to_datetime(df['Date & Time'])

    if rows is not None:
        dff = pd.DataFrame(rows)
        if len(dff.index) < len(df.index):
            [derived_virtual_selected_rows.append(i) for i in range(len(df.index), len(df.index))]
        df = df.iloc[derived_virtual_selected_rows]

    Mag_ref = 4
    size_ref = 12

    return html.Div([
        html.Div([
            # Magnitude graph
            dcc.Graph(
                id='Mag',
                figure={
                    'data': [
                        {
                            'x': df['Date & Time'],
                            'y': df['Mag'],
                            'mode': 'markers',
                            'marker': {
                                'size': df['Mag']/Mag_ref*size_ref,
                                'cmin': np.min(-df['Mag']),
                                'cmax': np.max(-df['Mag']),
                                'color': -df['Mag'],
                                'colorscale': 'Viridis',
                                'line': {'width': 1, 'color': 'rgb(0,0,0)'},
                                       }
                        }
                    ],
                    'layout': {
                        'title': 'Magnitude development over time',
                        'xaxis': {'automargin': True, 'title': 'Time'},
                        'yaxis': {'automargin': True, 'title': 'Magnitude', 'zeroline': False},
                        'height': 400,
                    },
                },
            )], style={'width': '49%', 'display': 'inline-block'},
        ),
        html.Div([
            # Frequency Magnitude Distribution
            dcc.Graph(
                id='FMD',
                figure={
                    'data': [
                        {
                            'x': np.sort(df['Mag']),
                            'y': list(range(len(df.index), 0, -1)),
                        }
                    ],
                    'layout': {
                        'title': 'Frequency Magnitude Distribution',
                        'xaxis': {'automargin': True, 'title': 'Magnitude'},
                        'yaxis': {'automargin': True, 'title': 'Number of events', 'type': 'log'},
                        'height': 400,
                        # 'margin': {'t': 50, 'l': 10, 'r': 10},
                    },
                },
            )], style={'width': '49%', 'display': 'inline-block'},
        ),
        html.Div([
            # Top view
            dcc.Graph(
                id='top view',
                figure={
                    'data': [
                        {
                            'x': df['x'],
                            'y': df['y'],
                            'mode': 'markers',
                            'marker': {
                                'size': df['Mag']/Mag_ref*size_ref,
                                'cmin': np.min(-df['Mag']),
                                'cmax': np.max(-df['Mag']),
                                'color': -df['Mag'],
                                'colorscale': 'Viridis',
                                'line': {'width': 1, 'color': 'rgb(0,0,0)'},
                                       }
                        }
                    ],
                    'layout': {
                        'title': 'Top view',
                        'xaxis': {'automargin': True, 'title': 'x [m]', 'zeroline': False},
                        'yaxis': {'automargin': True, 'title': 'y [m]', 'scaleanchor': 'x', 'scaleratio': 1, 'zeroline': False},
                        'height': 400,
                        #'margin': {'t': 10, 'l': 10, 'r': 10},
                    },
                },
            )], style={'width': '33%', 'display': 'inline-block'},
        ),
        html.Div([
            # Top view
            dcc.Graph(
                id='XZ view',
                figure={
                    'data': [
                        {
                            'x': df['x'],
                            'y': df['z'],
                            'mode': 'markers',
                            'marker': {
                                'size': df['Mag']/Mag_ref*size_ref,
                                'cmin': np.min(-df['Mag']),
                                'cmax': np.max(-df['Mag']),
                                'color': -df['Mag'],
                                'colorscale': 'Viridis',
                                'line': {'width': 1, 'color': 'rgb(0,0,0)'},
                                       }
                        }
                    ],
                    'layout': {
                        'title': 'Side view (xz)',
                        'xaxis': {'automargin': True, 'title': 'x [m]', 'zeroline': False},
                        'yaxis': {'automargin': True, 'title': 'z [m]', 'scaleanchor': 'x', 'scaleratio': 1, 'zeroline': False},
                        'height': 400,
                        #'margin': {'t': 10, 'l': 10, 'r': 10},
                    },
                },
            )], style={'width': '33%', 'display': 'inline-block'},
        ),
        html.Div([
            # Top view
            dcc.Graph(
                id='YZ view',
                figure={
                    'data': [
                        {
                            'x': df['y'],
                            'y': df['z'],
                            'mode': 'markers',
                            'marker': {
                                'size': df['Mag']/Mag_ref*size_ref,
                                'cmin': np.min(-df['Mag']),
                                'cmax': np.max(-df['Mag']),
                                'color': -df['Mag'],
                                'colorscale': 'Viridis',
                                'line': {'width': 1, 'color': 'rgb(0,0,0)'},
                                       }
                        }
                    ],
                    'layout': {
                        'title': 'Side view (yz)',
                        'xaxis': {'automargin': True, 'title': 'y [m]', 'zeroline': False},
                        'yaxis': {'automargin': True, 'title': 'z [m]', 'scaleanchor': 'x', 'scaleratio': 1, 'zeroline': False},
                        'height': 400,
                        #'margin': {'t': 10, 'l': 10, 'r': 10},
                    },
                },
            )], style={'width': '33%', 'display': 'inline-block'},
        ),
        html.Div([
            # 3D scatter plot
            dcc.Graph(
                id='3D',
                figure={
                    'data': [
                        {
                            'x': df['x'],
                            'y': df['y'],
                            'z': df['z'],
                            'mode': 'markers',
                            'type': 'scatter3d',
                            'marker': {
                                'size': df['Mag'] / Mag_ref * size_ref,
                                'cmin': np.min(-df['Mag']),
                                'cmax': np.max(-df['Mag']),
                                'color': -df['Mag'],
                                'colorscale': 'Viridis',
                                'line': {'width': 1, 'color': 'rgb(0,0,0)'},
                            }
                        }
                    ],
                    'layout': {
                        'title': '3D scatter of events',
                        'xaxis': {'automargin': True, 'title': 'x [m]', 'zeroline': False},
                        'yaxis': {'automargin': True, 'title': 'y [m]', 'scaleanchor': 'x', 'scaleratio': 1, 'zeroline': False},
                        'zaxis': {'automargin': True, 'title': 'z [m]', 'scaleanchor': 'x', 'scaleratio': 1, 'zeroline': False},
                        'height': 600,
                        # 'margin': {'t': 10, 'l': 10, 'r': 10},
                    },
                },
            )], style={'width': '100%', 'display': 'inline-block'},
        ),
    ]
    )


def dashboard(param):
    if platform == 'darwin':
        os.system('open http://127.0.0.1:8050/')
    app.run_server(debug=False)
