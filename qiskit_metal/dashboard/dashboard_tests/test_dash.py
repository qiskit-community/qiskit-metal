import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv'
)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H3('Row'),
        dcc.Dropdown(id='df_row',
                     options=[{
                         'label': i,
                         'value': i
                     } for i in range(df.shape[0])],
                     value=0,
                     placeholder='Row'),
    ],
             style={'display': 'inline-block'}),
    html.Div([
        html.H3('Column'),
        dcc.Dropdown(id='df_column',
                     options=[{
                         'label': i,
                         'value': i
                     } for i in range(df.shape[1])],
                     value=0,
                     placeholder='Column'),
    ],
             style={'display': 'inline-block'}),
    dash_table.DataTable(
        id='datatable-row-ids',
        columns=[{
            'name': i,
            'id': i,
            'deletable': True
        } for i in df.columns],
        data=df.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        row_selectable='multi',
        row_deletable=True,
        selected_rows=[],
        page_action='native',
        page_current=0,
        page_size=10,
    ),
    html.Div([
        html.H3(id='country',
                style={
                    'display': 'inline-block',
                    'padding': '5px'
                }),
        html.H3(id='key', style={
            'display': 'inline-block',
            'padding': '5px'
        }),
        html.H3(id='value', style={
            'display': 'inline-block',
            'padding': '5px'
        })
    ],
             style={'display': 'inline-block'}),
    html.Div(id='datatable-row-ids-container')
])


@app.callback([
    Output('datatable-row-ids', 'active_cell'),
    Output('datatable-row-ids', 'selected_cells'),
    Output('country', 'children'),
    Output('key', 'children'),
    Output('value', 'children'),
], [
    Input('df_row', 'value'),
    Input('df_column', 'value'),
])
def update_active_and_selected_cell(row, column):
    row = 0 if row is None else row
    column = 0 if column is None else column
    selected_cells = [{
        "row": row,
        "column": column,
        "column_id": df.columns[column]
    }]
    active_cell = {
        "row": row,
        "column": column,
        "row_id": df.country[row],
        "column_id": df.columns[column]
    }
    return active_cell, selected_cells, '{}\'s '.format(
        df.country[row]), '{}:'.format(df.columns[column]), df.iat[row, column]


@app.callback(Output('datatable-row-ids', 'style_data_conditional'), [
    Input('df_row', 'value'),
])
def highlight_row(row):
    return [{
        "if": {
            "row_index": row
        },
        "backgroundColor": "teal",
        'color': 'white'
    }]


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port='5000')