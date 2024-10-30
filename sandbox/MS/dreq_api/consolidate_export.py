import json
import os
import re
import sys
import warnings

# TODO: remove after initial "sandbox" dev period
add_paths = ["../../JA", "../../GR"]
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)

from logger import get_logger  # noqa

# UID generation
default_count = 0
default_template = "default_{:d}"

# Filtered records
filtered_records = []


def _map_record_id(record, records, keys):
    """
    Identifies a record_id in list of records using key.
    """
    global filtered_records
    matches = []
    # For each of the specified "keys", check if there is an entry in "records" that matches with "record"
    for key in keys:
        if key in record:
            recval = record[key]
            matches_tmp = [
                r for r, v in records.items() if key in v and v[key] == recval
            ]
            matches = [m for m in matches_tmp if m not in filtered_records]
            if len(matches) == 1:
                break
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        if len(matches_tmp) == 0:
            raise KeyError(f"No matches when consolidating '{record}' via '{keys}'.")
    else:
        raise KeyError(f"Multiple matches when consolidating '{record}'.")


def _map_attribute(attr, records, key):
    """
    Identifies a record_id in list of records using key and matching with the attribute value.
    """
    global filtered_records
    # For the specified "key", check if there is an entry in "records" that matches with "attr"
    matches_tmp = [r for r, v in records.items() if key in v and v[key] == attr]
    matches = [m for m in matches_tmp if m not in filtered_records]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        if len(matches_tmp) == 0:
            raise KeyError(f"No matches when consolidating '{attr}' via '{key}'.")
    else:
        raise KeyError(f"Multiple matches when consolidating '{attr}' via '{key}'.")


def map_data(data, mapping_table):
    """
    Maps the data to the one-base structure using the mapping table.

    Parameters
    ----------
    data : dict
        Three-base or one-base Airtable export.
    mapping_table dict
        The mapping table to apply to map to one base.

    Returns
    -------
    dict
        Mapped data with one-base structure.

    Note
    ----
        Returns the input dict if the data is already one-base.
    """
    logger = get_logger()
    missing_bases = []
    missing_tables = []
    mapped_data = {"Data Request": {}}

    # Reset filtered records
    global filtered_records
    if filtered_records:
        filtered_records = []

    if len(data.keys()) in [3, 4]:

        # Get filtered records
        for table, mapinfo in mapping_table.items():
            if (
                mapinfo["source_base"] in data
                and mapinfo["source_table"] in data[mapinfo["source_base"]]
            ):
                if "internal_filters" in mapinfo:
                    filters = mapinfo["internal_filters"]
                    for record_id, record in data[mapinfo["source_base"]].items():
                        filter_results = []
                        for filter_key, filter_val in filters.items():
                            if filter_key not in record:
                                filter_results.append(False)
                            elif filter_val["operator"] == "nonempty":
                                filter_results.append(bool(record[filter_key]))
                            elif filter_val["operator"] == "in":
                                if isinstance(record[filter_key], list):
                                    filter_results.append(
                                        any(
                                            fj in filter_val["values"]
                                            for fj in record[filter_key]
                                        )
                                    )
                                else:
                                    filter_results.append(
                                        record[filter_key] in filter_val["values"]
                                    )
                            elif filter_val["operator"] == "not in":
                                if isinstance(record[filter_key], list):
                                    filter_results.append(
                                        all(
                                            fj not in filter_val["values"]
                                            for fj in record[filter_key]
                                        )
                                    )
                                else:
                                    filter_results.append(
                                        record[filter_key] not in filter_val["values"]
                                    )
                        if not all(filter_results):
                            filtered_records.append(record_id)

        # Perform mapping in case of three-base structure
        for table, mapinfo in mapping_table.items():
            intm = mapinfo["internal_mapping"]
            if (
                mapinfo["source_base"] in data
                and mapinfo["source_table"] in data[mapinfo["source_base"]]
            ):
                # Copy the selected data to the one-base structure
                logger.debug(f"Mapping '{mapinfo['source_base']}' -> '{table}'")
                mapped_data["Data Request"][table] = {
                    **data[mapinfo["source_base"]][mapinfo["source_table"]],
                    "records": {
                        record_id: record
                        for record_id, record in data[mapinfo["source_base"]][
                            mapinfo["source_table"]
                        ]["records"].items()
                        if record_id not in filtered_records
                    },
                }

                # If record attributes require mapping
                if intm != {}:
                    # for each attribute that requires mapping
                    for attr in intm.keys():
                        for record_id, record in data[mapinfo["source_base"]][
                            mapinfo["source_table"]
                        ]["records"].items():
                            if (
                                attr not in record
                                or record[attr] is None
                                or record[attr] == ""
                                or record[attr] == []
                            ):
                                logger.debug(
                                    f"{table}: Attribute '{attr}' not found for record '{record_id}'."
                                )
                                continue
                            attr_vals = record[attr]

                            # operation
                            if intm[attr]["operation"] == "split":
                                attr_vals = re.split(r"\s*,\s*", attr_vals)
                            elif intm[attr]["operation"] == "":
                                if isinstance(attr_vals, str):
                                    attr_vals = [attr_vals]
                            else:
                                raise ValueError(
                                    f"Unknown internal mapping operation for attribute '{attr}' ('{mapinfo['source_table']}'): '{intm[attr]['operation']}'"
                                )

                            # Get mapped record_ids
                            # entry_type - single record_id or list of record_ids
                            # - map by record_id
                            if intm[attr]["entry_type"] == "record_id":
                                if not intm[attr]["base_copy_of_table"]:
                                    raise ValueError(
                                        "A copy of the table in the same base is required if 'entry_type' is set to 'record_id', "
                                        f"but 'base_copy_of_table' is set to False: '{mapinfo['source_table']}' - '{attr}'"
                                    )
                                elif not intm[attr]["base"] in data:
                                    raise KeyError(
                                        f"Base '{intm[attr]['base']}' not found in data."
                                    )
                                elif (
                                    intm[attr]["base_copy_of_table"]
                                    not in data[mapinfo["source_base"]]
                                ):
                                    raise KeyError(
                                        f"Table '{intm[attr]['table']}' not found in base '{intm[attr]['base_copy']}'."
                                    )
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    # The record copy in the current base
                                    record_copy = data[mapinfo["source_base"]][
                                        intm[attr]["base_copy_of_table"]
                                    ]["records"][attr_val]
                                    # The entire list of records in the base of origin
                                    recordlist = data[intm[attr]["base"]][
                                        intm[attr]["table"]
                                    ]["records"]
                                    recordID_new = _map_record_id(
                                        record_copy,
                                        recordlist,
                                        intm[attr]["map_by_key"],
                                    )
                                    if recordID_new:
                                        recordIDs_new.append(recordID_new)
                            # entry_type - name (eg. unique label or similar)
                            # - map by attribute value
                            elif intm[attr]["entry_type"] == "name":
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    recordID_new = _map_attribute(
                                        attr_val,
                                        data[intm[attr]["base"]][intm[attr]["table"]][
                                            "records"
                                        ],
                                        (
                                            intm[attr]["map_by_key"]
                                            if isinstance(intm[attr]["map_by_key"], str)
                                            else intm[attr]["map_by_key"][0]
                                        ),
                                    )
                                    if recordID_new:
                                        recordIDs_new.append(recordID_new)
                            else:
                                raise ValueError(
                                    f"Unknown 'entry_type' specified for attribute '{attr}' ('{mapinfo['source_table']}'): '{intm[attr]['entry_type']}'"
                                )
                            if not recordIDs_new:
                                raise KeyError(
                                    f"{table} (record '{record_id}'): For attribute '{attr}' no records could be mapped."
                                )
                            mapped_data["Data Request"][table]["records"][record_id][
                                attr
                            ] = recordIDs_new

            else:
                if mapinfo["source_base"] not in data:
                    missing_tables.append(mapinfo["source_base"])
                elif mapinfo["source_table"] not in data[mapinfo["source_base"]]:
                    missing_bases.append(mapinfo["source_table"])
        if len(missing_bases) > 0:
            warnings.warn(
                f"Encountered missing bases when consolidating the data: {set(missing_bases)}"
            )
        if len(missing_tables) > 0:
            warnings.warn(
                f"Encountered missing tables when consolidating the data: {missing_tables}"
            )
        return mapped_data
    # Return the data if it is already one-base
    elif len(data.keys()) == 1:
        return {"Data Request": next(iter(data.values()))}
    else:
        raise ValueError("The loaded Data Request has an unexpected data structure.")
