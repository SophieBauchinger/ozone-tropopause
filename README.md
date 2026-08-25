Climatological tropopause definition allowing the derivation of tropopause-relative potential temperature from ozone measurements in the upper troposphere and lower stratosphere.

## Background
The ozone climatology is based on global soundings from 1980-2025 combined with ERA5 reanalysis data including tropopause information. 

<img width="1232" height="615" alt="o3_flowchart_JOINT" src="https://github.com/user-attachments/assets/16844ade-22e2-40dc-9ebb-fceca6f01510" />

## Getting started
### Prerequisites 
* Python 3.8+
* 
### Installation (using pip)
1. Clone the repository
   ```
   git clone [https://github.com/Sophie](https://github.com/SophieBauchinger/ozone-tropopause.git)
   cd ozone-tropopause
   ```
2. Install dependencies
   ```
   pip install -r requirements.txt 
   ```

### Usage
To check that everything is working properly, run the following: `python tests.py `

Import the main function into your python scripts with  

```from ozone-tropopause.o3_chemical_tropopause import coord_val_from_O3``` 

The function takes O3-values, (equivalent) latitude and date/month information in a variety of formats and returns the derived values of $\Delta\Theta(\text{O}_3)$ and corresponding data flags in the same data type. 
