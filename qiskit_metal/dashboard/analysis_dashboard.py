import dash
from dash import Dash as WebDash
from jupyter_dash import JupyterDash

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State, MATCH, ALL

import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from numpy import ndarray

import plotly.express as px

import pandas as pd

import numpy as np
from traitlets.traitlets import default

from .ad_toolbox import create_dropdown_table, selected_datatable_to_df, browse_datatable_to_df, row_exists, merge_df


class AnalysisDashboard():
    """Allows the user to see predefined graphs and create custom ones interactively
    """

    def __init__(self,
                 mode: str = "notebook",
                 renderer=None,
                 default_graph_data: dict = None):
        """Allows the user to see predefined graphs and create custom ones interactively

        Args:
            mode (str, optional): "notebook" or "web" depending on if the user wants to run the
            dashboard in a jupyter notebook or on the web. Defaults to "notebook".
            renderer ('QAnalysisRenderer', optional): A quantum analysis object. Defaults to None.
            default_graph_data (dict, optional): A dict containing data for the default graph section
            of the dashboard. Defaults to None.
        """
        self.mode = mode
        self.renderer = renderer
        self.all_data = self.renderer.get_data()
        self.default_graph_data = default_graph_data
        self.non_plot_data = {}
        self.plot_data = {}
        self.__format_data(self.all_data, self.default_graph_data)
        self.__add_plot_data()
        self.graphs = 0

        if self.mode == "notebook":
            self.app = JupyterDash(__name__,
                                   external_stylesheets=[dbc.themes.BOOTSTRAP])
        elif self.mode == "web":
            self.app = WebDash(__name__,
                               external_stylesheets=[dbc.themes.BOOTSTRAP])

    def run_app(self):
        """Runs the dashboard in a jupyter notebook or on the web.
        """
        self.__create_layout()
        if self.__using_notebok():
            self.app.run_server(mode="inline")
        else:  #this isnt really right
            self.app.run_server(debug=True)

    def __create_layout(self):
        """Creates the layout for the dashbaord.
        """
        self.app.layout = dbc.Container([
            dbc.Row(dbc.Col(html.H3("Premade graphs")), className="mb-2"),
            dbc.Row([
                dbc.Col(
                    dcc.Graph(figure=px.scatter(self.default_graph_data[graph]).
                              update_traces(mode='lines+markers')))
                for graph in self.default_graph_data
            ], "default-graph-container"),
            dbc.Row(dbc.Col(html.H3("Browse data")), className="mb-2"),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id={
                            "type": "dataframe-dropdown",
                            "index": 1
                        },
                        options=[{
                            "label": key,
                            "value": key
                        } for key in self.plot_data],
                    ),),
                dbc.Col()
            ],
                    "dataframe-dropdown-main-container",
                    className="mb-2"),
            dbc.Row([
                dbc.Col([], "dataframe-dropdown-secondary-container"),
                dbc.Col()
            ],
                    className="mb-2"),
            dbc.Row(dbc.Col([], "dataframe-dropdown-table-container"),
                    className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Button("Add selected row/column",
                               "add-selected-data",
                               className="mr-1"),
                    dbc.Button("Add selected cell",
                               "add-selected-cell",
                               className="mr-1"),
                    dbc.Button(
                        "Add table rows", "add-all-rows", className="mr-1"),
                    dbc.Button("Add tables columns",
                               "add-all-columns",
                               className="mr-1"),
                ])
            ],
                    "button-container",
                    className="mb-2 row d-none"),
            dbc.Row(dbc.Col(dash_table.DataTable(id="selected-data-datatable")),
                    "selected-data",
                    className="mb-2"),
            html.Div([], "graph-container", className="mb-2"),
            dbc.Row(dbc.Col(
                dbc.Button("New graph", "add-graph-button", color="success")),
                    className="mb-2"),
        ])

        @self.app.callback(
            Output("dataframe-dropdown-secondary-container", "children"),
            Output("dataframe-dropdown-table-container", "children"),
            Output("add-selected-cell", "disabled"),
            Output("button-container", "className"),
            Input({
                "type": "dataframe-dropdown",
                "index": ALL
            }, "value"),
            State("dataframe-dropdown-secondary-container", "children"))
        def handle_dropdown(dropdowns, secondary_children):  #redo
            """Handles the dropdown selection and creates a corresponding DataTable.

            Args:
                dropdowns (list): A list of slection values from the dropdowns.
                secondary_children (dcc.Dropdown): The current state of the secodnary dropdown menu.

            Returns:
                second_dropdown (dcc.Dropdown): Either a dropdown or empty depending on the first dropdown selected value
                table (dash_table.DataTable): A DataTable containing data from the dropdown selections
                add_cell_button_status (boolean): Status of if the add-selected-cell is clickable
                class_name (str): A CSS styling string
            """
            second_dropdown = []
            table = []
            add_cell_button_status = True
            class_name = "mb-2"
            if dropdowns[0]:  # 1 is full
                if isinstance(self.plot_data[dropdowns[0]], dict):  # 1 is dict
                    if len(dropdowns) > 1:  # 2 exists
                        second_dropdown = secondary_children
                        if dropdowns[1]:  # 2 is full
                            add_cell_button_status = False
                            table = create_dropdown_table(
                                self.plot_data[dropdowns[0]][dropdowns[1]])
                        else:  # 2 is empty
                            class_name += " row d-none"
                    else:  # 2 doesnt exist
                        class_name += " row d-none"
                        second_dropdown = dcc.Dropdown(
                            id={
                                "type": "dataframe-dropdown",
                                "index": 2
                            },
                            options=[{
                                "label": key,
                                "value": key
                            } for key in self.plot_data[dropdowns[0]]])
                else:  # 1 is not dict
                    table = create_dropdown_table(self.plot_data[dropdowns[0]])
            else:  # 1 is empty
                class_name += " row d-none"
            return second_dropdown, table, add_cell_button_status, class_name

        #add selected data to table
        @self.app.callback(Output("selected-data", "children"), [
            Input("add-selected-data", "n_clicks"),
            Input("add-selected-cell", "n_clicks"),
            Input("add-all-rows", "n_clicks"),
            Input("add-all-columns", "n_clicks")
        ], [
            State("dataframe-output", "data"),
            State("dataframe-output", "selected_rows"),
            State("dataframe-output", "selected_columns"),
            State("dataframe-output", "active_cell"),
            State("selected-data-datatable", "data"),
            State("selected-data-datatable", "columns"),
            State({
                "type": "dataframe-dropdown",
                "index": ALL
            }, "value"),
        ])
        def add_choosen_data(selected_r_c, selcted_cell, all_rows, all_columns,
                             input_table_data, selected_rows, selected_columns,
                             input_active_cell, output_table_data,
                             output_columns, dropdown_values):
            """Adds selected data from the browse DataTable to the selected DataTable.

            Args:
                selected_r_c ([type]): [description]
                selcted_cell ([type]): [description]
                all_rows ([type]): [description]
                all_columns ([type]): [description]
                input_table_data ([type]): [description]
                selected_rows ([type]): [description]
                selected_columns ([type]): [description]
                input_active_cell ([type]): [description]
                output_table_data ([type]): [description]
                output_columns ([type]): [description]
                dropdown_values ([type]): [description]

            Returns:
                [type]: [description]
            """
            button_clicked = str(
                dash.callback_context.triggered[0]["prop_id"].split(".")[0])
            if output_columns and output_table_data:  # output table exists
                table_df = browse_datatable_to_df(output_table_data,
                                                  output_columns)
            else:  #output table doenst exist
                table_df = pd.DataFrame()
            if input_table_data:  # input table exists
                if button_clicked == "add-all-rows":  # add all rows clicked
                    selected_rows = range(len(input_table_data))
                    selected_columns = []
                if button_clicked == "add-all-columns":  # add all columns clicked
                    selected_rows = []
                    selected_columns = [
                        col for col in input_table_data[0].keys()
                    ]
                if button_clicked == "add-selected-cell":  # add selecetd cell clicked
                    if input_active_cell:  # a cell is selected
                        row = input_active_cell["row"]
                        column = input_active_cell["column"]
                        key = "{}_{}_r{}_c{}".format(dropdown_values[0],
                                                     dropdown_values[1], row,
                                                     column)
                        if not row_exists(key, table_df):
                            dict_dfs = self.plot_data[dropdown_values[0]]
                            df_data = []
                            for df in dict_dfs:
                                df_data.append(dict_dfs[df].iloc[row, column])
                            df = pd.DataFrame([df_data])
                            df.insert(0, "Data", key)
                            table_df = merge_df(df, table_df)
                else:  # hanldes adding-all-rows, add-all-columns, and add-seleceted-data
                    if selected_rows:
                        for selected_row in selected_rows:
                            key = "{}_r{}".format(dropdown_values[0],
                                                  selected_row)
                            if not row_exists(key, table_df):
                                row = input_table_data[selected_row]
                                df_data = [row[col] for col in row]
                                df = pd.DataFrame([df_data])
                                df.insert(0, "Data", key)
                                table_df = merge_df(df, table_df)
                    if selected_columns:
                        for selected_column in selected_columns:
                            key = "{}_c{}".format(dropdown_values[0],
                                                  selected_column)
                            if not row_exists(key, table_df):
                                df_data = [
                                    row[selected_column]
                                    for row in input_table_data
                                ]
                                df = pd.DataFrame([df_data])
                                df.insert(0, "Data", key)
                                table_df = merge_df(df, table_df)
            table = dash_table.DataTable(id="selected-data-datatable",
                                         columns=[{
                                             "name": str(i),
                                             "id": str(i)
                                         } for i in table_df.columns],
                                         data=table_df.to_dict("records"),
                                         row_deletable=True)
            return dbc.Col(table)

        #create graphs
        @self.app.callback(Output("graph-container", "children"),
                           Input("add-graph-button", "n_clicks_timestamp"),
                           State("graph-container", "children"),
                           State("selected-data-datatable", "data"))
        def create_new_graph(clicked, cur_children, data):
            """Handles "new graph" button clicks. Dynamically creates new graph containers
             that allows users to interact with simulation data


            Args:
                clicked ([type]): [description]
                cur_children ([type]): [description]
                data ([type]): [description]

            Returns:
                [type]: [description]
            """
            if clicked and data:
                self.graphs += 1
                clicks = clicked
                axis_options = [{"label": "Auto", "value": "Auto"}]
                data_options = []
                for row in data:
                    axis_options.append({
                        "label": row["Data"],
                        "value": row["Data"]
                    })
                    data_options.append({
                        "label": row["Data"],
                        "value": row["Data"]
                    })
                # data_options.append({
                #     "label": "Compare axes",
                #     "value": "compare_axes"
                # })
                if cur_children is None:
                    cur_children = []
                cur_children.append(
                    html.Div(
                        id={
                            "type": "dynamic-graph-container",
                            "index": clicks
                        },
                        children=[
                            dbc.Row([
                                dbc.Col([
                                    html.H3("Graph {}".format(self.graphs)),
                                    dbc.Button(id={
                                        "type": "dynamic-delete-graphs",
                                        "index": clicks
                                    },
                                               children="Delete graph",
                                               color="danger",
                                               className="mr-1",
                                               size="sm")
                                ])
                            ]),
                            dbc.Row([
                                dbc.Col(id="dropdown_parent",
                                        children=[
                                            html.H5("Data"),
                                            dbc.Checklist(id={
                                                "type": "data-checklist",
                                                "index": clicks
                                            },
                                                          options=data_options,
                                                          labelStyle={
                                                              'display':
                                                                  'inline-block'
                                                          }),
                                            html.H5("y-axis type"),
                                            dbc.RadioItems(
                                                options=[
                                                    {
                                                        "label": "Log",
                                                        "value": "Log"
                                                    },
                                                    {
                                                        "label": "Linear",
                                                        "value": "Linear"
                                                    },
                                                ],
                                                value="Linear",
                                                id={
                                                    "type": "log-toggle-button",
                                                    "index": clicks
                                                },
                                            ),
                                        ]),
                                dbc.Col([
                                    html.H5("x-axis scale"),
                                    dcc.Dropdown(
                                        id={
                                            "type": "x-axis-dropdown",
                                            "index": clicks
                                        },
                                        options=axis_options,
                                        value=axis_options[0]["value"]),
                                    html.H5("y-axis scale"),
                                    dcc.Dropdown(id={
                                        "type": "y-axis-dropdown",
                                        "index": clicks
                                    },
                                                 options=axis_options,
                                                 value=axis_options[0]["value"])
                                ]),
                            ],
                                    className="mt-2 mb-4"),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id={
                                        "type": "dynamic-graph",
                                        "index": clicks
                                    },
                                              figure={}))
                            ])
                        ]))

                return cur_children
            return cur_children

        @self.app.callback(
            Output({
                "type": "dynamic-graph-container",
                "index": MATCH
            }, "children"),
            Input({
                "type": "dynamic-delete-graphs",
                "index": MATCH
            }, "n_clicks"),
            State({
                "type": "dynamic-graph-container",
                "index": MATCH
            }, "children"))
        def delete_graph(clicks, children):
            """Deletes graph containers.

            Args:
                clicks ([type]): [description]
                children ([type]): [description]

            Returns:
                [type]: [description]
            """
            if clicks:
                # self.graphs -= 1
                return html.Div()
            return children

        #fill graphs
        @self.app.callback(
            Output({
                "type": "dynamic-graph",
                "index": MATCH
            }, "figure"), [
                Input({
                    "type": "data-checklist",
                    "index": MATCH
                }, "value"),
                Input({
                    "type": "x-axis-dropdown",
                    "index": MATCH
                }, "value"),
                Input({
                    "type": "y-axis-dropdown",
                    "index": MATCH
                }, "value"),
                Input({
                    "type": "log-toggle-button",
                    "index": MATCH
                }, "value")
            ], [
                State("selected-data-datatable", "data"),
                State("selected-data-datatable", "columns"),
                State({
                    "type": "dynamic-graph",
                    "index": MATCH
                }, "figure")
            ])
        def update_figure_data(data_values, x_axis_value, y_axis_value,
                               log_toggle, data, columns,
                               figure):  #come back for log stuff
            """Handles users input within graph containers to create the graph.

            Args:
                data_values ([type]): [description]
                x_axis_value ([type]): [description]
                y_axis_value ([type]): [description]
                log_toggle ([type]): [description]
                data ([type]): [description]
                columns ([type]): [description]
                figure ([type]): [description]

            Returns:
                [type]: [description]
            """
            fig = figure
            table_df = selected_datatable_to_df(data)
            df_data = {}
            dff = pd.DataFrame([0])
            if data_values:
                for value in data_values:
                    if value in table_df.columns:
                        df_data[value] = table_df[value]
                dff = pd.DataFrame(df_data)
            fig = px.scatter(dff)
            fig.update_traces(mode='lines+markers')
            fig.update_yaxes(type="linear" if log_toggle == "Linear" else "log")
            if x_axis_value != "Auto" and x_axis_value is not None:
                x_axis_ticks = table_df[x_axis_value].tolist()
                fig.update_layout(xaxis=dict(
                    tickmode='array',
                    tickvals=x_axis_ticks,
                    range=[np.nanmin(x_axis_ticks),
                           np.nanmax(x_axis_ticks)]))

            if y_axis_value != "Auto" and y_axis_value is not None:
                y_axis_ticks = table_df[y_axis_value].tolist()
                fig.update_layout(yaxis=dict(
                    tickmode='array',
                    tickvals=y_axis_ticks,
                    range=[np.nanmin(y_axis_ticks),
                           np.nanmax(y_axis_ticks)]))
            fig.update_layout(
                {'margin': go.layout.Margin(l=10, r=10, b=10, t=10, pad=10)})

            return fig

    ####################
    # Helper functions #
    ####################

    def __add_plot_data(self):
        data = self.all_data
        for key in data:
            if isinstance(data[key], dict):
                self.plot_data[str(key)] = data[key]
            elif isinstance(data[key], pd.DataFrame):
                self.plot_data[str(key)] = data[key]
            else:
                self.non_plot_data[str(key)] = data[key]
        self.all_data = None

    def __format_data(self, *args):
        for data in args:
            self.__rec_format_data(data)

    def __rec_format_data(self, data):
        for key in data:
            if isinstance(data[key], dict):
                self.__rec_format_data(data[key])
            elif isinstance(data[key], ndarray):
                data[key] = pd.DataFrame(data[key])

    def __using_notebok(self):
        if self.mode == "notebook":
            return True
        elif self.mode == "web":
            return False
        else:
            return TypeError  #do this better