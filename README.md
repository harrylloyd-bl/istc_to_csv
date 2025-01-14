# ISTC_to_csv
#### ISTC YAML to CSV conversion 
`istc_to_csv` converts raw [ISTC](https://data.cerl.org/istc/_search) yaml exports to flat CSV format for ease of analysis.

## Install
Copy the repository with `git clone`, then create the environment.
  
### pip
```
$ python -m pip install -r requirements.txt
```

### conda/mamba
The environment name will be `istc`.
```
$ mamba create -f environment.yml
```

The dependencies are:
- pandas
- pyyaml
- tqdm

## Use
You can get a copy of the raw data by searching for 'ISTC' on the British Library [research repository](https://bl.iro.bl.uk).
Put the raw file in the data/raw/ directory.
The code to run the conversion is contained in `istc_to_csv/dataset.py`. Once you set up the Python environment and downloaded the raw yaml data you can run the conversion:
```
$ python istc_to_csv/dataset.py
```
The process should take ~ 10 minutes on a standard laptop. The majority of this is loading the yaml, so if you can install the [LibYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)
bindings the process will be faster. Note you may need to uninstall and reinstall pyyaml to add the LibYAML bindings.

## Outputs
Outputs will go to `data/processed`, and consist of 7 csv files. Consult the data dictionary in the `docs` folder for more info.

The basic outputs are:
- core.csv
  - All non-repeating fields as columns per ISTC work
  - The only output with a guaranteed unique index
- holdings.csv
  - Information on holdings information for each ISTC work
- imprints.csv
  - Information on imprints for each ISTC work
- references.csv
  - References for each ISTC work
- related_resources.csv
  - Related resources for each ISTC work

The derived outputs are:
- core_holdings.csv
  - The core table with the holdings table joined on 
- core_imprints.csv
  - The core table with the imprints table joined on


## Project Organization

```
├── LICENSE            <- MIT License
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final data sets.
│   └── raw            <- The original, immutable data dump.
│
├── references         <- Data dictionary for the core, holdings and imprints output csvs.
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
└── istc_to_csv        <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes istc_to_csv a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    └── dataset.py              <- Script to generate data
```
--------
Code was developed by Harry Lloyd, Research Software Engineer, British Library. Contact harry.lloyd [at] bl.uk.
Version 1.0.0 of the code has a DOI [![DOI](https://zenodo.org/badge/901373558.svg)](https://doi.org/10.5281/zenodo.14644509)  

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>