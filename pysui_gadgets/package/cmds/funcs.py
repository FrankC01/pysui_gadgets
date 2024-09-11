#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""Package function commands and utilities."""

from typing import Any

from pysui.sui.sui_txresults.package_meta import (
    SuiMoveScalarArgument,
    SuiMoveVector,
    SuiParameterReference,
    SuiMoveParameterType,
    SuiParameterStruct,
    SuiMoveFunction,
    SuiMoveModule,
)
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui_gadgets.utils.filters import (
    filter_modules_excluding,
    filter_modules_with_including,
    filter_modules_with_entry_points,
)


def _sig_parm_types(holder: list, sig: str) -> str:
    """."""
    if holder:
        tlen = len(holder)
        tcount = 0
        sig += "<"
        for abiltity_set in holder:
            if "constraints" in abiltity_set:
                sig += f"T{tcount}: {' + '.join(abiltity_set['constraints'])}"
                tcount += 1
                if tcount < tlen:
                    sig += ", "
            else:
                sig += f"T{tcount}"
        sig += ">"
    return sig


def _func_sig(fname: str, dfunc: pgql_type.MoveFunctionGQL) -> str:
    """_func_sig Builds the signature prefix.

    :param fname: Function name
    :type fname: str
    :param dfunc: Function object
    :type dfunc: SuiMoveFunction
    :return: Signature prefix
    :rtype: str
    """
    sig = ""
    if dfunc.is_entry:
        sig = f"public entry fun {fname}"
    elif dfunc.visibility == "PUBLIC":
        sig = f"public fun {fname}"
    else:
        sig = f"fun {fname}"
    # Setup type abilities
    sig = _sig_parm_types(dfunc.type_parameters, sig) + "("
    return sig


def _new_func_params(parm: Any, sig: str) -> str:
    """_new_func_params Incrementally builds argument or return list.

    :param parm: Input function argument or return data type
    :type parm: Any
    :param sig: Accumulator
    :type sig: str
    :raises AttributeError: If type of parm is not handled
    :return: signature current state
    :rtype: str
    """
    if fparms := parm.get("signature"):
        if sref := fparms.get("ref"):
            sig += sref
        if sbody := fparms.get("body"):
            if isinstance(sbody, str):
                sig += sbody
            elif dtype := sbody.get("datatype"):
                if dtype.get("package"):
                    sig += (
                        dtype.get("package")
                        + "::"
                        + dtype.get("module")
                        + "::"
                        + dtype.get("type")
                    )
                    if tpars := dtype.get("typeParameters"):
                        sig += "<"
                        sig += ",".join(
                            ["T" + str(x.get("typeParameter")) for x in tpars]
                        )
                        sig += ">"
    return sig


def _build_func_signature(func_desc: dict[str, pgql_type.MoveFunctionGQL]) -> str:
    """_build_func_signature Builds a functions signature string.

    :param func_desc: Dictionary with func_name:func_definition
    :type func_desc: dict[str, pgql_type.MoveFunctionGQL]
    :return: Signature string
    :rtype: str
    """
    # Get name and function
    func_name, func_entry = list(func_desc.items())[0]
    # Setup initial signature
    sig = _func_sig(func_name, func_entry)

    # Build Signature argument
    parm_count = len(func_entry.parameters)
    parm_index = 0
    for parm in func_entry.parameters:
        sig = _new_func_params(parm, sig)
        if parm_index + 1 < parm_count:
            sig += ", "
        parm_index = parm_index + 1

    # Build Signature return
    if func_entry.returns:
        parm_count = len(func_entry.returns)
        parm_index = 0
        retsig = ") : "
        if parm_count > 1:
            retsig += "("
        for parm in func_entry.returns:
            retsig = _new_func_params(parm, retsig)
            if parm_index + 1 < parm_count:
                retsig += ", "
            parm_index = parm_index + 1
        if parm_count > 1:
            retsig += ")"
        sig += retsig
    else:
        sig += ")"
    return sig


def print_function_signatures(
    raw_mods: list[pgql_type.MoveModuleGQL],
    includes: set,
    excludes: set,
    nonentries: bool,
) -> None:
    """function_signatures Generate function signatures from package's modules.

    :param mods: Package's modules dictionary
    :type mods: dict[str, SuiMoveModule]
    :param args: Filtering criteria
    :type args: argparse.Namespace
    """
    mods: dict[str, pgql_type.MoveModuleGQL] = {
        module.module_name: module for module in raw_mods
    }

    if includes:
        modules = filter_modules_with_including(
            mods=mods, includes=includes, nonentries=nonentries
        )
    elif excludes:
        modules = filter_modules_excluding(
            mods=mods, excludes=excludes, nonentries=nonentries
        )
    else:
        modules = filter_modules_with_entry_points(mods=mods, nonentries=nonentries)

    # modules = _filter_functions(mods, args)
    for mod_key, mod_func_list in modules.items():
        print(f"For module {mod_key}")
        for func_hit in mod_func_list:
            print(_build_func_signature(func_hit))
