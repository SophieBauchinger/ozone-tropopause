""" Test if the function is working and can access the climatology files """

import pandas as pd
import random
import numpy as np
import xarray as xr

from o3_chemical_tropopause import coord_val_from_O3

N = int(1e4)
o3_rand = [random.gauss(60,30)+(0 if i%3 else random.random()*800) for i in range(N)]
eql_rand = [random.uniform(-90,90) for i in range(N)]
month_rand = [random.choice(range(1,13)) for i in range(N)]

# test float
out = coord_val_from_O3(o3_rand[int(N/2)], eql_rand[int(N/2)], month_rand[int(N/2)])
print(f'{str(float):<45} ->   {type(out[0])}')

# test list
out = coord_val_from_O3(o3_rand, eql_rand, month_rand)
print(f'{str(list):<45} ->   {type(out[0])}')

# test numpy.ndarray
out = coord_val_from_O3(np.array(o3_rand), 
                        np.array(eql_rand), 
                        np.array(month_rand))
print(f'{str(np.ndarray):<45} ->   {type(out[0])}')

# test pd.Series
out = coord_val_from_O3(pd.Series(o3_rand), 
                        pd.Series(eql_rand), 
                        pd.Series(month_rand))
print(f'{str(pd.Series):<45} ->   {type(out[0])}')

# test pd.DataFrame
data = pd.DataFrame({'o3':o3_rand, 'eql': eql_rand, 'mon': month_rand})
out = coord_val_from_O3('o3', 'eql', 'mon', data = data)
print(f'{str(pd.DataFrame):<45} ->   {type(out[0])}')

# text xr.DataArray
out = coord_val_from_O3(xr.DataArray(o3_rand, dims='time'), 
                        xr.DataArray(eql_rand, dims='time'),
                        xr.DataArray(month_rand, dims='time'))
print(f'{str(xr.DataArray):<45} ->   {type(out[0])}')

# Test plotting
coord_val_from_O3(o3_rand, eql_rand, month_rand, plot=True)
