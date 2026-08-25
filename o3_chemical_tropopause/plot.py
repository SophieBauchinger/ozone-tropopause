import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import xarray as xr

from tools import to_da

# Plot results (before casting to input type)
def control_plots(valid_tp_interp, o3_da, eql_da, mon_da): 
    """ Show result of applying chemical tropopause to the given data. 
        Called from within `coord_val_from_O3`.

    Parameters: 
        valid_tp_interp (xr.Dataarray): 
        o3_da (xr.Dataarray): O3 observation values
        eql_da (xr.Dataarray): Equivalent latitudes
        mon_da (xr.Dataarray): Months

    """   
    # Colors and month labels 
    colors = [
        '#ffcf67','#e5a659','#cc824d',
        '#b16243','#92463b','#712f3a',
        '#572949','#4c396b','#4e5593',
        '#5877b5','#6498ce','#72bee6']
    labels = ['Jan','Feb','Mar',
              'Apr','May','Jun',
              'Jul','Aug','Sep',
              'Oct','Nov','Dec']
    cmap1 = mcolors.ListedColormap(colors) # month
    norm = mcolors.Normalize(1,13)
    cmap2 = plt.colormaps['magma'].resampled(18) # eql

    fig,(ax0,ax1,cax) = plt.subplots(1,3, figsize=(10,4), dpi=100,
                                     width_ratios=[0.5,0.5,0.02], layout='tight')
    # Data: Highlights for Month/Eql.Lat
    ax0.scatter(o3_da, valid_tp_interp, c=mon_da,
                cmap = cmap1, norm=norm)
    img = ax1.scatter(o3_da, valid_tp_interp, c=eql_da, cmap=cmap2)

    # Legend and Colorbar 
    leg0 = ax0.legend(handles = [
        Line2D([0],[0], marker='o', ls='None', 
               color=cmap1(norm(m)), 
               label=labels[m-1]) 
            for m in range(1,7)],
               loc='upper left')
    ax0.legend(handles = [
        Line2D([0],[0], marker='o', ls='None', 
               color=cmap1(norm(m)), 
               label=labels[m-1]) 
            for m in range(7,13)],
               loc='lower right')
    ax0.add_artist(leg0)
    fig.colorbar(img, cax=cax, label='Equivalent latitude', aspect=40,)
    
    # Axis labels
    ax0.set_ylabel(r"Derived $\Delta\Theta\,(O_3)$ [K]")
    for ax in [ax0,ax1]: 
        ax.set_xlabel("O$_3$ [ppb]")
        ax.grid(ls='dotted', lw=1, color='lightgrey')
        ax.set_axisbelow(True)
    
    plt.show()

#%% Plot output/flag with additional input data
def plot_results(tp_interp_out, flag_out, o3_vals, coord_data, coord_label=None):
    """ Plot the resulting tp_interp_out and flag onto the given coord_data"""

    tp_interp_da = to_da(tp_interp_out, 'o3_tp')
    flag_da = to_da(flag_out, 'flag')
    o3_da = to_da(o3_vals, 'o3')
    coord_da = to_da(coord_data, 'coord')
    tp_interp_da, flag_da, o3_vals, coord_da = xr.align(tp_interp_da, flag_da, o3_da, coord_da, join="exact")

    fig, axs = plt.subplots(
        2,2,figsize=(6,5), dpi=150, width_ratios=[0.8,0.03],)
    (ax_res, cax, ax_flag, lax) = axs.flat
    lax.axis('off')
    img = ax.scatter(o3_da, coord_da, c=tp_interp_da, cmap='berlin', s=6)
    fig.colorbar(img, cax=cax, label=r"Derived $\Delta\Theta(O_3)$ [K]",
                 aspect=60)
    plot_flag(ax_flag, flag_da, o3_da, coord_da)
    for ax in [ax_res,ax_flag]:
        ax.set_ylabel(coord_label)
    fig.tight_layout()

def plot_flag(ax, flag_da, o3_da, coord_da): 
    """ """
    c_dict = {
        -1 : '#B680A7',
        0  : "#A8DADC",
        1  : "#40A96D",
        2  : "#457B9D",
        9  : "#A3476A",
        }
    flag_dict = {
        -1 : 'NaN input',
        0  : 'Good',
        1  : r'TROP, no $\Delta_{{TP}}$',
        2  : r'STRAT, no $\Delta_{{TP}}$',
        9  : 'No climatology',
    }

    for flag in [0,-1,1,2,9]:
        ax.scatter(o3_da[flag_da==flag], 
                   coord_da[flag_da==flag], 
                   color = c_dict[int(flag)], 
                   label = flag_dict[int(flag)],
                   s=6)

    handles = [Line2D([0],[0], ls='None', marker='o',color=c) 
               for c in c_dict.values()] # larger dots for legend
    ax.legend(handles, flag_dict.values())
    ax.set_xlabel('O3 [ppb]')       
    return 

def plot_var_on_tp_interp(tp_interp_out, var_data, var_label): 
    """ Plot another variable as a function of tp_interp. """
    tp_da = to_da(tp_interp_out, 'o3_tp')
    var_da = to_da(var_data, 'var')
    tp_da, var_da = xr.align(tp_da, var_da, join='exact')

    fig,ax=plt.subplots()
    ax.scatter(var_da, tp_da)
    ax.set_xlabel(var_label)
    ax.set_ylabel(r"Derived $\Delta\Theta(O_3)$ [K]")

    return fig,ax
