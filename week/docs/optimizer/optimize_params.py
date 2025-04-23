from docs.database import OptimizeParams, get_table_data


optimize_params = get_table_data(OptimizeParams, conditions=OptimizeParams.id == 1)[0]

