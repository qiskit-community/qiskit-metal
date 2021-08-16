import datetime
from typing import Dict

import dash
from dash import Dash as WebDash
from jupyter_dash import JupyterDash

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH, ALL
import plotly.express as px
import pandas as pd

import dash_bootstrap_components as dbc

# from qiskit_metal.analyses.quantization import ScatteringImpedanceSim
# from qiskit_metal.analyses.quantization import LumpedElementsSim
# from qiskit_metal.analyses.quantization import EigenmodeSim

# Only using for testing ################
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

design = designs.DesignPlanar({}, True)
design.chips.main.size['size_x'] = '2mm'
design.chips.main.size['size_y'] = '2mm'

design.delete_all_components()

q1 = TransmonPocket(
    design,
    'Q1',
    options=dict(pad_width='425 um',
                 pocket_height='650um',
                 connection_pads=dict(
                     readout=dict(loc_W=+1, loc_H=+1, pad_width='200um'))))

# sims = {
#     "SI": ScatteringImpedanceSim,
#     "LE": LumpedElementsSim,
#     "EM": EigenmodeSim
# }
################################


class Visualizer():

    def __init__(self, mode: str = "notebook"):
        self.mode = mode
        self.sim = sims['SI'](design, 'hfss')  #fix this

        if self.mode == "notebook":
            self.app = JupyterDash(__name__,
                                   external_stylesheets=[dbc.themes.BOOTSTRAP])
        elif self.mode == "web":
            self.app = WebDash(__name__,
                               external_stylesheets=[dbc.themes.BOOTSTRAP])

    def __create_layout(self):
        #Web app layout
        self.app.layout = html.Div([
            html.H2("Upload design (gds file)"),
            dcc.Upload(id='upload-image',
                       children=html.Div([html.Button('Upload File')]),
                       multiple=False),
            html.Div(id='output-image-upload'),
            html.H2("Choose your simulation"),
            html.Div([
                dcc.RadioItems(id='sim-input',
                               options=[{
                                   'label': 'Scattering Impedance',
                                   'value': 'SI'
                               }, {
                                   'label': 'Lumped Elements',
                                   'value': 'LE'
                               }, {
                                   'label': 'Eigenmode',
                                   'value': 'EM'
                               }],
                               value='SI')
            ]),
            html.H2("Update setup"),
            html.Div([
                html.Div(id='sim-output', children=[], className="col"),
                html.Div(id='setup-output', className="col"),
                html.Div(id='self-sim-output', className="col")
            ],
                     className="row"),
            html.Div(
                children=[html.Button(id='save-sim-setup', children='Button')]),
        ])

        #controls file upload
        @self.app.callback(Output('output-image-upload', 'children'),
                           Input('upload-image', 'contents'),
                           State('upload-image', 'filename'),
                           State('upload-image', 'last_modified'))
        def upload_file(list_of_contents, list_of_names, list_of_dates):
            if list_of_contents is not None:
                return parse_file_upload(list_of_names, list_of_dates)

        def parse_file_upload(filename, date):
            return html.Div([
                html.H5(filename),
                html.H6(datetime.datetime.fromtimestamp(date)),
            ])

        #choose simulation type
        @self.app.callback(Output('sim-output', 'children'),
                           Input('sim-input', 'value'),
                           State('sim-output', 'children'))
        def simulation_choice(input_value, children):
            children = []
            self.sim = sims[input_value](design, "hfss")  #dont alwasy use hfss\
            # print(self.sim.setup.sim)
            return extract_setup_dict(self.sim.setup.sim, children, 0)

        #extracts setup varibales from simulation for modification
        def extract_setup_dict(setup_dict, children, index):
            for key in setup_dict:
                if isinstance(setup_dict[key], dict):
                    new_child = extract_setup_dict(setup_dict[key], children,
                                                   index)
                    index += 1
                else:
                    new_child = html.Div(id={
                        'type': 'dynamic-inputs-labels',
                        'index': index,
                    },
                                         key=str(key),
                                         children=[
                                             html.Div(html.B(key)),
                                             dcc.Input(id={
                                                 'type': 'dynamic-inputs',
                                                 'index': index,
                                             },
                                                       value=str(
                                                           setup_dict[key]))
                                         ])
                    children.append(new_child)
                index += 1
            return children

        #changes and displays sim.setup.sim when input boxes are modified
        @self.app.callback(Output('setup-output', 'children'),
                           Input({
                               'type': 'dynamic-inputs',
                               'index': ALL
                           }, 'value'),
                           Input({
                               'type': 'dynamic-inputs-labels',
                               'index': ALL
                           }, 'key'))
        def display_setup_dict(values, keys):
            return html.Div(
                str(
                    set_display_setup_dict(self.sim.setup.sim, [], 0,
                                           values)[1]))

        #helper function
        def set_display_setup_dict(sim_dict, children, index, updated_values):
            for key in sim_dict:
                if isinstance(sim_dict[key], dict):
                    new_child, sim_dict[key] = set_display_setup_dict(
                        sim_dict[key], children, index, updated_values)
                    index += 1
                else:
                    if updated_values:
                        sim_dict[key] = updated_values[index]
                    new_child = html.Div(sim_dict[key])
                    children.append(new_child)
                index += 1
            return children, sim_dict

        # @self.app.callback(Output('self-sim-output', 'children'),
        #                    Input('save-sim-setup', 'n_clicks'))
        # def confirm_setup(n_clicks):
        #     return html.Div([
        #         html.Div('{} -> {}'.format(key, self.sim.setup.sim[key]))
        #         for key in self.sim.setup.sim
        #     ])

    def run_app(self):
        self.__create_layout()
        if self.__using_notebok():
            self.app.run_server(mode="inline")
        else:  #this isnt really right
            self.app.run_server(debug=True)

    def __using_notebok(self):
        if self.mode == "notebook":
            return True
        elif self.mode == "web":
            return False
        else:
            return TypeError  #do this better
