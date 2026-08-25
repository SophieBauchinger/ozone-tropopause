import numpy as np
import pandas as pd
import xarray as xr

# Helper functions
def to_da(x, name, data=None):
    """ Cast input to DataArray. 'data' must be given if 'x' is a string. """
    if isinstance(x, str):
        if data is None: raise ValueError(f'`data` must be given if {name}={x}') 
        return to_da(data[x], x) 
    if isinstance(x, xr.DataArray): 
        return x
    if isinstance(x, xr.Dataset): 
        return x[name]
    return xr.DataArray(
        np.atleast_1d(x), dims='obs', name=name)
    
def get_month(x, data=None): 
    """ Returns array of month if given months or datetime object. """
    da = to_da(x, 'month', data)
    if np.issubdtype(da.dtype, np.datetime64): 
        return da.dt.month
    return da

def restore_type(result, template): 
    """ Cast result to the dtype and structure of template if possible. """
    if np.isscalar(template): 
        return float(result.values[0])
    if isinstance(template, np.ndarray): 
        return result.values
    if isinstance(template, list): 
        return list(result.values)
    if isinstance(template, (pd.Series, pd.DataFrame)): 
        return pd.Series(result.values, index=template.index)
    if isinstance(template, (xr.DataArray, xr.Dataset)): 
        return xr.DataArray(result.values, coords=template.coords, dims=template.dims)
    return result.values
