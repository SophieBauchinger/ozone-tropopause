# -*- coding: utf-8 -*-
"""
@Author: Sophie Bauchinger, IAU
@Date: Tue Apr 07 15:55:32 2026

Main logic to retrieve tropopause-relative values per O3 observation 
from the ozone climatology. 

Reference Tropopause-IDs: 
 * dPT_dyn35 (potential temperature distance to the local 3.5 PVU surface)
 * dPT_therm (potential temperature distance to the local WMO tropopause)
 
Flags in order of priority of assignment:
    FLAG_NAN = -1       # original data is NaN
    FLAG_GOOD = 0       # valid delta-TP derived
    FLAG_BELOW = 1      # certain troposphere, but uncertain delta-TP
    FLAG_ABOVE = 2      # certain stratosphere, but uncertain delta-TP
    FLAG_CLIM = 9       # no valid climatology available 

""" 
import numpy as np
import xarray as xr
import pandas as pd

from tools import to_da, get_month, restore_type
from plot import *

#%% Apply climatological / chemical O3-tropopause definition to measurements 

def load_clim(tp_id): 
    """ Load coordinate-specific dataset into memory. """
    fname = f'{tp_id}_ozone_climatology.nc'
    with xr.open_dataset(fname) as ds: 
        ds = ds
    return ds

CLIMATOLOGIES = {tp_id : load_clim(tp_id) for tp_id in ['dPT_dyn35', 'dPT_therm']}

def coord_val_from_O3(o3_vals, eql_vals, date_info, tp_id='dPT_dyn35', data=None, plot=False): 
    """ Get the interpolated representative value from O3 measurements in the given eqlrange and month. 

    Parameters: 
        o3_val (array_like, float | str): 
            O3 measurement(s) in ppb
        eql_val (array_list, float | str): 
            Equivalent latitude of each measurement
        date_info (array_list, int): 
            Date or Month of the year of each measurement
        tp_id (str): 
            Reference tropopause definition, must be one of 'dPT_dyn35' or 'dPT_therm' 
        data (xr.Dataset|pd.DataFrame): 
            Optional. Must be given if o3_vals/eql_vals/date_info are strings.  
        plot (bool): 
            Show control plots

    Returns the corresponding value(s) of `tp_coord` that best fits the given `o3_vals`.
    """
    # Normalise inputs and align dimensions
    o3_da = to_da(o3_vals, 'o3', data)
    eql_da = to_da(eql_vals, 'eql', data)
    mon_da = get_month(date_info, data)

    o3_da, eql_da, mon_da = xr.align(o3_da, eql_da, mon_da, join="exact")
    
    # Get climatology
    ds = CLIMATOLOGIES[tp_id]
    subset = ds['mean_ozone'].sel(
        eqlat=eql_da,
        month=mon_da,
        method='nearest',
    )

    def interp_foo(o3, o3_clim, tp_vals):
        """ Wrapper for numpy interp. with set arguments. """
        return np.interp(o3, o3_clim, tp_vals, left=-9999, right=9999)

    tp_interp = xr.apply_ufunc(
        interp_foo,
        o3_da,
        subset, # o3 reference
        subset['tp_val'], # reference coordinate
        input_core_dims=[[], ['tp_val'], ['tp_val']],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[float],
    )

    # Flags in order of priority of assignment:
    FLAG_NAN = -1       # original data is NaN
    FLAG_GOOD = 0       # valid delta-TP derived
    FLAG_BELOW = 1      # certain troposphere, but uncertain delta-TP
    FLAG_ABOVE = 2      # certain stratosphere, but uncertain delta-TP
    FLAG_CLIM = 9       # no valid climatology available 

    # create flag
    flag_da = xr.full_like(tp_interp, FLAG_GOOD)
    mask_nan = np.isnan(o3_da) | np.isnan(eql_da) | np.isnan(mon_da)
    mask_below = tp_interp.isin(-9999)
    mask_above = tp_interp.isin(9999)
    flag_da = flag_da\
        .where(~np.isnan(tp_interp), FLAG_CLIM)\
        .where(~mask_below, FLAG_BELOW)\
        .where(~mask_above, FLAG_ABOVE)\
        .where(~mask_nan, FLAG_NAN)

    # remove "-9999/9999" values
    valid_tp_interp = tp_interp.where((~np.isnan(tp_interp)) & (abs(tp_interp)<9000)) 
    
    out_template = (o3_vals if not isinstance(o3_vals, str) else data)
    tp_interp_out = restore_type(valid_tp_interp, out_template)
    flag_out = restore_type(flag_da, out_template)
    
    if plot: 
        control_plots(valid_tp_interp, o3_da, eql_da, mon_da)

    return tp_interp_out, flag_out
