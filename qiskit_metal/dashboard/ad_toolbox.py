import pandas as pd
import dash_table


def create_dropdown_table(df):
    """Creates a Dash DataTable from the "Browse data" dropdown selection.

    Args:
        df (pd.DataFrame): DataFrame provided from the simulation object's get_data function

    Returns:
        table (dash_table.DataTable): DataTable containing data from inputted DataFrame
    """
    data = df.to_dict("records")
    columns = [{
        "name": str(i),
        "id": str(i),
        "selectable": True
    } for i in df.columns]
    table = dash_table.DataTable(id="dataframe-output",
                                 data=data,
                                 columns=columns,
                                 row_selectable="multi",
                                 column_selectable="multi",
                                 selected_rows=[],
                                 selected_columns=[])
    return table


def selected_datatable_to_df(table_data):
    """Creates a DataFrame from the inputted DataTable data. The data is from
        the DataTable containing all the users selected data.

    Args:
        table_data (list): Data extracted from the selected data DataTable

    Returns:
        dff (pd.DataFrame): DataFrame with data from inputted DataTable
    """
    data = {}
    for row in table_data:
        row_values = list(row.values())
        size = len(row_values) - 1
        data_values = row_values[:size]
        key_value = row_values[size]
        data[key_value] = data_values
    dff = pd.DataFrame(data=data)
    dff.index.names = ["Passes"]
    return dff


def browse_datatable_to_df(table_data, columns):
    """Creates a DataFrame from the inputted DataTable data. The data is from
        the DataTable containing all the browsable data from the simulation object.


    Args:
        table_data (list): Data extracted from the browse data DataTable

    Returns:
        dff (pd.DataFrame): DataFrame with data from inputted DataTable
    """
    df = pd.DataFrame(table_data, columns=[str(c["name"]) for c in columns])
    df.set_index("Data")
    return df


def row_exists(value, df):
    """Checks if a row with the value is contained in the DataFrame extracted using the selected_datatable_to_df
        method. This avoids duplicate rows being added to the selected data DataTable

    Args:
        value (str): the value being checked for in the df
        df (pd.DataFrame): a DataFrame from the selected_datatable_to_df method

    Returns:
        boolean: whether or not a row exists in the DataFrame
    """
    if "Data" in df.columns:
        for row in df["Data"]:
            if value == row:
                return True
    return False


def merge_df(*args):
    if len(args) > 1:
        df1 = pd.DataFrame(args[0])
        args = args[1:]
        for arg in args:
            df2 = pd.DataFrame(arg)
            new_cols = {x: y for x, y in zip(df1.columns, df2.columns)}
            df_out = df2.append(df1.rename(columns=new_cols))
            df1 = df_out
        return df_out
    return args
