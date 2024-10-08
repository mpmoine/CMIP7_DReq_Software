#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data request example of the API usage.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import pprint
from collections import defaultdict

# Import API (for users, only second one will be needed, first is to prepare json database)
from dump_transformation import read_json_input_file_content, transform_content, write_json_output_file_content
from data_request import DataRequest


# Json file names
input_json_file = "../../CMIP7_DReq_Content/airtable_export/dreq_raw_export.json"
output_DR_json_file = "DR_request_basic_dump2.json"
output_VS_json_file = "VS_request_basic_dump2.json"

# Step 1: Prepare json databases for data request and vocabulary server
content = read_json_input_file_content(input_json_file)
data_request, vocabulary_server = transform_content(content)
write_json_output_file_content(output_DR_json_file, data_request)
write_json_output_file_content(output_VS_json_file, vocabulary_server)

# Step 2: Build Data Request
DR = DataRequest.from_separated_inputs(DR_input_filename=output_DR_json_file, VS_input_filename=output_VS_json_file)

# Or step 1-2:
DR = DataRequest.from_input(json_input_filename=input_json_file)

# Step 3: Get information from Data Request
# -> Print DR content
print(DR)
# -> Print an experiment group content
print(DR.experiments_groups["recz5nwuvKpkr1fss"])
# -> Get all variables' id associated with an opportunity
print(DR.find_variables_per_opportunity("recD45ipnmfCTBH7B"))
# -> Get all experiments' id associated with an opportunity
print(DR.find_experiments_per_opportunity("recD45ipnmfCTBH7B"))
# -> Get information about the shapes of the variables of all variables groups
rep = dict()
rep_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for elt in DR.get_variables_groups():
	rep[elt.id] = dict(cell_methods=set(), frequency=set(), temporal_shape=set(), variables=set())
	for var in elt.get_variables():
		var_info = elt.vs.get_variable(element_id=var, default="???")
		rep[elt.id]["cell_methods"].add(var_info.get("cell_methods", "???"))
		rep[elt.id]["frequency"].add(var_info.get("frequency", "???"))
		rep[elt.id]["temporal_shape"].add(var_info.get("temporal_shape", "???"))
		rep[elt.id]["variables"].add(var_info.get("mip_variables", "???"))
		rep_data[elt.id][var_info.get("frequency", "???")][var_info.get("temporal_shape")].append(var_info.get("mip_variables"))

pprint.pprint(rep)
pprint.pprint(rep_data)
