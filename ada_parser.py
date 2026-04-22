import os
import sys
import copy
import logging
import libadalang as lal
from typing import List, Dict, TypedDict, Mapping
from pathlib import Path


LOGGER = logging.getLogger("AdaParserLogger")
LOGGER.addHandler(logging.FileHandler('ada_parser_logger_output.log', mode='w'))


class PayloadField(TypedDict):
    """A single entry in a message payload dictionary entry"""
    name: str
    default: int
    size: int # bit-width of field


class MessagePayload(TypedDict):
    """Full payload entry for the message dictionary"""
    name: str
    fields: List[PayloadField]


MESSAGE_DICT: Dict[str, MessagePayload] = {}

def add_dict_entry(
    name: str,
    fields: List[Mapping[str, int]],
) -> None:
    """
    Adds a new entry to the message dictionary
    """
    MESSAGE_DICT[name] = {
        "name": name,
        "fields": list(fields), # shallow copy to protect dictionary entry
    }


def get_record_rep_clause(file, record_name):

    # Find record in Ada source if it was not already found and loaded into the internal dictionary
    if record_name not in MESSAGE_DICT:
        record, fields = _get_record_rep_clause(file, record_name)

        # Add to dictionary when valid
        if record and fields:
            LOGGER.info(f"Successfully loaded {record_name} from {file}")
            add_dict_entry(
                name=record_name,
                fields=fields,
            )
        else:
            return None, None

    return copy.deepcopy(MESSAGE_DICT[record_name])



def _get_record_rep_clause(file, record_name):
    """
    Gets a Dictionary representation of a message (record) from Ada source 
    """
    results = (None, [])
    ctx = lal.AnalysisContext()
    unit = ctx.get_from_file(file)
    if unit.diagnostics:
        LOGGER.warning(f"Could not find unit file {unit}")
        return results
    LOGGER.info(f"Successfully loaded {unit}")

    # Get and verify if any RecordRepClauses were found in file
    record_rep_clause = lambda node: node.is_a(lal.RecordRepClause)
    rep_clauses = unit.root.findall(record_rep_clause)
    if rep_clauses == []:
        LOGGER.warning(f"No RecordRepClauses found for unit {unit}")
        return results
    
    # Get and verify the specified record in file
    for record in rep_clauses:
        if record.f_name.text == record_name:
            LOGGER.info(f"Found record {record_name} in {unit}")
            # Iterate through each component in record
            for component in record.f_components:
                # Field should be a ComponentClause, otherwise issue.
                # ComponentClause should have f_range attributes to indicate first .. last bits
                if not component.is_a(lal.ComponentClause):
                    LOGGER.error(f"Component {component.f_id.text} is not a ComponentClause and may not have a valid bit range (f_bit .. l_bit)")
                    return results
                
                bin_range = component.f_range.f_range
                # Values from Ada need to accomodate for 0 indexing
                right = bin_range.f_right.p_denoted_value + 1
                _, fields = results
                fields.append({"name": component.f_id.text, "default": 0, "size": right})

            # Return early when done with all components in record
            return results
        
    LOGGER.error(f"Unexpected error in get_record_rep_clause() for file={file}, record_name={record_name}")
    return results
     
