
# CMIP7 Data Request Software

This repository is for development of python code to allow users to interact programatically with the [CMIP7 data request](https://wcrp-cmip.org/cmip7/cmip7-data-request/). 
It will provide an API and scripts that can produce lists of the variables requested for each CMIP7 experiment, information about the requested variables, and in general support different ways of querying and utilizing the information in the data request.


## v1.0beta release

The latest **official release** (21 Oct 2024) is tagged as `v1.0beta`. 
During the `v1.0beta` release period leading up to the next official release (`v1.0` on 22 November 2024) those trying out the software can use either:
- The `v1.0beta` tag
- The latest stable version, which will be the most recent commmit on the `main` branch.

**This software is under active development** and will evolve substantially during the `v1.0beta` release period. 
Accordingly we encourage users to try the latest stable version in order to access the latest features.

The next sections provide a brief overview of the software and explain how to get started.
**While the software is a work in progress, the Data Request Task Team encourages user feedback to help us improve upcoming versions.**
We are releasing a beta version at an early stage of development in order to maximize community input into its design.
Here are some ways to provide feedback during the `v1.0beta` release:
- For specific questions or issues (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For more general questions or concerns, such as suggestions for new features, contribute to the software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).



## Overview

The CMIP7 data request **software** and **content** are version controlled in separate github repositories.
Official releases of the data request correspond to a tag in each of these repositories (e.g., `v1.0beta`). 
However the software can interact with different versions of the content - for example, to examine changes that have occurred when a new version of the data request is issued.

The data request **content**, which is version controlled [here](https://github.com/CMIP-Data-Request/CMIP7_DReq_Content), refers to the information comprising the data request. 
This includes descriptions of Opportunities and their lists of requested variables, definitions of the variables, etc.
The content is stored as `json` and read by the data request software as its input, but users should not interact with this `json` directly and its structure is not designed for readability.
Users do not need to manually download the content as this is done automatically by the software (see "Getting Started", below, for further details).

The data request content is an automatic export from Airtable, a cloud platform used by the Data Request Task Team to facilitate ongoing community engagement in developing the data request.
Airtable provides users with a browseable web interface to explore data request information contained in relational databases that are referred to as "bases".
These Airtable bases contain interlinked tables that constitute the primary source of data request information.

The content of each official release of the data request can be explored online using the Airtable interface.
This provides a browseable web view of the content, allowing users to follow links between different elements of the data request - for example, to view the variables requested by a given Opportunity, or to view the Opportunities that request a given variable.
This view is complementary to the access to the content that is provided via the software, and both access methods (Airtable and software) are based on the same underlying information content.


Using the data request **software** provides a way to interact programmatically with the data request content, such as to:

- Given a list of supported opportunities and their priorities, produce lists of variables to output for each experiment
- Output the CF-compliant metadata characterizing each variable, as needed by CMOR
- Compare the requested output of CMIP7 experiments to a given model's published CMIP6 output
- Estimate output volumes

The software should facilitate integration of the data request into modelling workflows.
Suggestions for functionality are welcome in the [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).


During development, the software and content repositories reside in the github organisation https://github.com/CMIP-Data-Request.
Stable releases will eventually be migrated into the https://github.com/WCRP-CMIP organisation.


## Getting started

To begin, clone the software and navigate to the `scripts/` directory:
```
git clone git@github.com:CMIP-Data-Request/CMIP7_DReq_Software.git
cd CMIP7_DReq_Software/scripts
```
The `env.yml` file can be used to create a conda environment in which to run the software:
```
conda env create -n my_dreq_env --file env.yml
```
replacing `my_dreq_env` with your preferred environment name. 
Activate this environmeent:
```
conda activate my_dreq_env
```
and run the the example script:
```
python workflow_example.py
```
This script contains a workflow to access the data request content, specify a list of Opportunities and priority levels of variables, and output the lists of variables requested from each experiment in the specified Opportunities.
Each listed variables is currently identified by a unique "compound name" using CMIP6-era table names and short variable names (`Amon.tas`, `Omon.tos`, etc).
Variable names may change in upcoming releases, but in any case a mapping to CMIP6-era variable names will be retained in the data request so as to allow comparison with CMIP6 output (for those variables that were defined in CMIP6).

To access the data request content, the example script first needs to identify the version of the data request content that is being used. 
This is done by specifying a tag in the content repo and calling the retrieval function.
For example:
```
use_dreq_version = 'v1.0beta'
dc.retrieve(use_dreq_version)
```
downloads `v1.0beta` of the content into local cache, if it is not already there.
The script can then access it by loading it into a python dict variable:
```
content = dc.load(use_dreq_version)
```
Currently a single version of the content `json` file is roughly 20 MB in size.
The size of local cache can be managed by deleting unused versions.
For example, to remove a specific version:
```
dc.delete(use_dreq_version)
```
Or to remove all locally cached versions:
```
dc.delete()
```
