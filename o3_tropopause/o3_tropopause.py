# -*- coding: utf-8 -*-
"""
@Author: Sophie Bauchinger, IAU
@Date: 07 Apr 2026
@Last updated: 26 Aug 2026

Main logic to retrieve tropopause-relative values per O3 observation 
from the ozone climatology. The ozone climatology must be monotonically 
increasing along `tp_val` for each eql. x month grid point. 

Reference Tropopause-IDs: 
 * dPT_dyn35
    Potential temperature distance to the local 3.5 PVU surface
 * dPT_therm 
    Potential temperature distance to the local WMO tropopause
 
The climatology is provided in 10° eql bins, observations with |eql| >= 30°
are assigned to the corresponding bin using nearest-neighbour lookup.
Observations in the tropics (|eql|<30°) are outside the climatological 
domain and receive FLAG_CLIM. 


Flags, in order of priority:
    FLAG_NAN = -1       # input data is NaN
    FLAG_CLIM = 9       # no usable climatology / outside clim. domain
    FLAG_BELOW = 1      # O3 below clim. range (exp. troposphere)
    FLAG_ABOVE = 2      # O3 above clim. range (exp. stratosphere)
    FLAG_GOOD = 0       # valid delta-TP derived

""" 
import numpy as np
import os
import pandas as pd
import xarray as xr

from tools import to_da, get_month, restore_type
from plot import control_plots

VALID_TP_IDS = ('dPT_dyn35', 'dPT_therm')

EQL_MIN_ABS = 30.0 

FLAG_NAN = -1 
FLAG_CLIM = 9  
FLAG_BELOW = 1
FLAG_ABOVE = 2
FLAG_GOOD = 0 

#%% Apply climatological / chemical O3-tropopause definition to measurements 

def load_clim(tp_id): 
    """ Load a coordinate-specific climatology into memory. """
    pdir = os.path.dirname(os.path.abspath(__file__)) + "/" # fetch directory of this file 
    fname = f'{tp_id}_ozone_climatology.nc'
    with xr.open_dataset(pdir+fname) as ds: 
        return ds.load()

CLIMATOLOGIES = {tp_id : load_clim(tp_id) for tp_id in VALID_TP_IDS}

def coord_val_from_O3(o3_vals, eql_vals, date_info, tp_id='dPT_dyn35', data=None, plot=False): 
    """ 
    Get the interpolated representative value from O3 measurements.
     
    The climatological O3-TP profile is selected by equivalent 
    latitude and month. Equivalent-latitude observations with 
    |eql| >= 30° are valid for lookup using nearest-neighbour selection. 

    Parameters 
    ----------
    o3_vals (array_like, float,  str): 
        O3 measurement(s) in ppb. A string must be a var. name in 'data'

    eql_vals (array_list, float,  str): 
        Equivalent latitude of each measurement. A string must be a var. name in 'data'

    date_info (array_list, int, str): 
        Month (1-12), date-like values. A string must be a var. name in 'data'

    tp_id (str): 
        Reference tropopause definition. Must be one of 'dPT_dyn35' or 'dPT_therm' 
    
    data (xr.Dataset|pd.DataFrame): 
        Optional. Input dataset/table used when any of `o3_vals`, `eql_vals` 
        or `date_info` are supplied as strings. 
    
    plot (bool): 
        Show control plots. Default=False

    Returns
    -------
    tp_interp_out, flag_out
        Tropopause-relative values and corresponding integer flags.
        Output structure follows the input where supported. 

    Notes
    -----
    Flag priority is 
        FLAG_NAN > FLAG_CLIM > FLAG_BELOW/FLAG_ABOVE > FLAG_GOOD
    """

    # Normalise inputs and align dimensions
    o3_da = to_da(o3_vals, 'o3', data)
    eql_da = to_da(eql_vals, 'eql', data)
    mon_da = get_month(date_info, data)

    o3_da, eql_da, mon_da = xr.align(o3_da, eql_da, mon_da, join="exact")

    # Input validation 
    if tp_id not in VALID_TP_IDS: 
        raise ValueError(f'Unknown tp_id={tp_id!r}. Expected one of {VALID_TP_IDS}')

    mask_nan = np.isnan(o3_da) | np.isnan(eql_da) | np.isnan(mon_da)
    mask_valid_eql = ~mask_nan & (np.abs(eql_da) >= EQL_MIN_ABS) # exclude tropics 
    eql_for_sel = eql_da.where(mask_valid_eql)

    # Get climatology
    clim_ds = CLIMATOLOGIES[tp_id]

    subset = clim_ds['mean_ozone'].sel(
        eqlat=eql_for_sel,
        month=mon_da,
        method='nearest',
    )

    # Determine the valid climatological O3 range
    o3_min = subset.min(dim='tp_val', skipna=True)
    o3_max = subset.max(dim='tp_val', skipna=True)

    mask_clim = (mask_valid_eql & o3_min.notnull() & o3_max.notnull())

    mask_below = mask_clim & (o3_da < o3_min)
    mask_above = mask_clim & (o3_da > o3_max)
    mask_good = mask_clim & ~mask_below & ~mask_above

    def interp_foo(o3, o3_clim, tp_vals):
        """ Wrapper for np.interp including NaN-checks. """
        valid = np.isfinite(o3_clim) & np.isfinite(tp_vals)
        if valid.sum() < 2:
            return np.nan
        return np.interp(o3, o3_clim[valid], tp_vals[valid])

    # Interpolate only valid 
    tp_interp = xr.apply_ufunc(
        interp_foo,
        o3_da.where(mask_good),
        subset,                     # climatological O3 profile
        subset['tp_val'],           # corresponding TP-rel coordinate
        input_core_dims=[[], ['tp_val'], ['tp_val']],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[float],
    )

    # Assign flags (subsequent calls override so that NaN is priority 1)
    flag_da = xr.full_like(tp_interp, FLAG_GOOD, dtype=int)

    flag_da = flag_da\
        .where(~mask_above, FLAG_ABOVE)\
        .where(~mask_below, FLAG_BELOW)\
        .where(mask_clim, FLAG_CLIM)\
        .where(~mask_nan,   FLAG_NAN) 
    
    out_template = (o3_vals if not isinstance(o3_vals, str) else data)
    tp_interp_out = restore_type(tp_interp, out_template)
    flag_out = restore_type(flag_da, out_template)
    
    if plot: 
        control_plots(tp_interp, o3_da, eql_da, mon_da)

    return tp_interp_out, flag_out
