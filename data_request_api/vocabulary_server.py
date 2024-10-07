#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vocabulary server.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy

from logger import get_logger
from dump_transformation import read_json_file


class VocabularyServer(object):
	def __init__(self, input_database, **kwargs):
		self.vocabulary_server = read_json_file(input_database)

	def get_variable(self, element_id, element_key=None, default=False):
		return self.get_element(element_table="data_request_opportunities_(public)", element_type="variables",
		                        element_id=element_id, element_key=element_key, default=default)

	def get_experiment(self, element_id, element_key=None, default=False):
		return self.get_element(element_table="data_request_opportunities_(public)", element_type="experiment",
		                        element_id=element_id, element_key=element_key, default=default)

	def get_element(self, element_table, element_type, element_id, element_key=None, default=False):
		logger = get_logger()
		if element_table in self.vocabulary_server:
			if element_type in self.vocabulary_server[element_table]:
				if element_id in self.vocabulary_server[element_table][element_type]["records"]:
					value = copy.deepcopy(self.vocabulary_server[element_table][element_type]["records"][element_id])
					if element_key is not None:
						if element_key in value:
							value = value[element_key]
						else:
							logger.error(f"Could not find key {element_key} of id {element_id} of type {element_type} "
							             f"in table {element_table} in the vocabulary server.")
							raise ValueError(f"Could not find key {element_key} of id {element_id} of type "
							                 f"{element_type} in table {element_table} in the vocabulary server.")
					return value
				elif default:
					logger.critical(f"Could not find id {element_id} of type {element_type} in table {element_table}"
					                f" in the vocabulary server.")
					return default
				else:
					logger.error(f"Could not find id {element_id} of type {element_type} in table {element_table} "
					             f"in the vocabulary server.")
					raise ValueError(f"Could not find id {element_id} of type {element_type} in table {element_table} "
					                 f"in the vocabulary server.")
			else:
				logger.error(f"Could not find element type {element_type} in table {element_table} "
				             f"in the vocabulary server.")
				raise ValueError(f"Could not find element type {element_type} in table {element_table} "
				                 f"in the vocabulary server.")
		else:
			logger.error(f"Could not find element table {element_table} in the vocabulary server.")
			raise ValueError(f"Could not find element table {element_table} in the vocabulary server.")
