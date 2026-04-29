import os
import sys
import copy
import logging
import libadalang as lal
from typing import List, Dict, TypedDict, Mapping
from pathlib import Path


LOGGER = logging.getLogger("AdaParserLogger")
LOGGER.setLevel(logging.DEBUG)
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
        # Attempt to find the record in the Ada source file
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
    # Create analysis context from GPR project
    project = lal.GPRProject("libadalang_parser.gpr")
    ctx = lal.AnalysisContext(unit_provider=project.create_unit_provider())

    # @NOTE: If using a project with subprojects, use a separate .gpr that does not include the subprojects
    # project = lal.GPRProject("libadalang_parser_nosub.gpr")
    # ctx = lal.AnalysisContext(unit_provider=project.create_unit_provider())

    # Get all record rep clauses from file
    unit = ctx.get_from_file(file)
    assert not unit.diagnostics, unit.diagnostics
    clauses = list(unit.root.findall(lal.RecordRepClause))

    # Get target record of specified name
    target = next(
        (c for c in clauses if c.f_name.text == record_name),
        None
    )

    if target is None:
        LOGGER.error(f"Could not find record {record_name} in {file}")
        return None, None

    results = (record_name, [])

    _, fields = results

    for comp in target.f_components:
        if not comp.is_a(lal.ComponentClause):
            LOGGER.error(f"Component {comp.f_id.text} is not a ComponentClause and may not have a valid bit range (f_bit .. l_bit)")
            return results
        
        rng = comp.f_range.f_range   # ".." BinOp
        lo = eval_bound(rng.f_left)
        hi = eval_bound(rng.f_right)
        size_bits = hi - lo + 1
    
        fields.append({"name": comp.f_id.text, "default": 0, "size": size_bits})

    return results
     

def eval_bound(expr):
    # Top-level "switch" on expression type.
    match True:
        case _ if expr.is_a(lal.IntLiteral):
            # Integer literal, just grab value
            return expr.p_denoted_value

        case _ if expr.is_a(lal.Identifier, lal.DottedName):
            # (RM 4.1.3)
            # selected_component ::= prefix . selector_name
            # selector_name ::= identifier | character_literal | operator_symbol
            #
            # Attempt to get referenced declaration if it exists.
            # This is how we traverse the AST to find the referenced declaration.
            decl = expr.p_referenced_decl(True)
            if decl is None:
                LOGGER.error(f"Unhandled bound case: unresolved name expression: {expr.text}")
                raise ValueError(f"Cannot resolve: {expr.text}")

            # Initializer can be exposed under different fields depending on
            # declaration kind (e.g. ObjectDecl vs NumberDecl).
            init = _get_decl_initializer(decl)
            if init is None:
                LOGGER.error(
                    "Unhandled bound case: resolved declaration has no initializer "
                    f"(decl kind: {decl.kind_name}, expr: {expr.text})"
                )
                raise ValueError(f"Resolved but no initializer: {decl.kind_name}")
            return eval_bound(init)

        case _ if expr.is_a(lal.BinOp):
            # Arithmetic expression (optional support)
            op = expr.f_op.text
            l = eval_bound(expr.f_left)
            r = eval_bound(expr.f_right)
            if op == "+":
                return l + r
            if op == "-":
                return l - r
            if op == "*":
                return l * r
            if op == "/":
                return l // r
            LOGGER.error(f"Unhandled bound case: unsupported binary operator '{op}' in expression: {expr.text}")
            raise ValueError(f"Unsupported op: {op}")

        case _ if expr.is_a(lal.CallExpr):
            # Type conversions are represented as calls in the AST, e.g.
            # Payload_Code (Base_Types.Code_Last_Bit). For bound evaluation we just
            # need the numeric value of the first actual argument.
            suffix = getattr(expr, "f_suffix", None)
            if suffix is None:
                LOGGER.error(f"Unhandled bound case: CallExpr has no suffix: {expr.text}")
                raise ValueError("CallExpr has no suffix to evaluate")

            # Single-arg call (conversion-like): T (Expr)
            if suffix.is_a(lal.AssocList) and len(suffix) == 1:
                assoc = suffix[0]
                actual = getattr(assoc, "f_r_expr", None)
                if actual is None:
                    LOGGER.error(f"Unhandled bound case: CallExpr association missing f_r_expr: {expr.text}")
                    raise ValueError("CallExpr association missing right expression")
                return eval_bound(actual)

            LOGGER.error(f"Unhandled bound case: unsupported CallExpr shape: {expr.text}")
            raise ValueError(f"Unsupported CallExpr shape: {expr.text}")

        case _:
            LOGGER.error(f"Unhandled bound case: unsupported node kind '{expr.kind_name}' for expression: {expr.text}")
            raise ValueError(f"Unsupported node: {expr.kind_name}")


def _get_decl_initializer(decl):
    """
    Return an expression node that initializes a declaration, if any.
    """
    # Direct declaration fields commonly used by libadalang decl nodes.
    for attr in ("f_expr", "f_default_expr", "f_default_value", "f_renaming_clause"):
        node = getattr(decl, attr, None)
        if node is not None:
            return node

    # Some references resolve to a defining name; parent is the declaration.
    parent = getattr(decl, "parent", None)
    if parent is not None:
        for attr in ("f_expr", "f_default_expr", "f_default_value", "f_renaming_clause"):
            node = getattr(parent, attr, None)
            if node is not None:
                return node

    return None
