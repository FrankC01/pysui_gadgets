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

from argparse import Namespace
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
            if abiltity_set.abilities:
                sig += f"T{tcount}: {' + '.join(abiltity_set.abilities)}"
                tcount += 1
                if tcount < tlen:
                    sig += ", "
            else:
                sig += f"T{tcount}"
        sig += ">"
    return sig


def _func_sig(fname: str, dfunc: SuiMoveFunction) -> str:
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
    elif dfunc.visibility == "Public":
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
    if isinstance(parm, str):
        sig += parm
    elif isinstance(parm, SuiParameterReference):
        sig += "&" if not parm.is_mutable else "&mut "
        sig = _new_func_params(parm.reference_to, sig)
    elif isinstance(parm, SuiParameterStruct):
        sig += parm.name
        if parm.type_arguments:
            sig += "<"
            for smpt in parm.type_arguments:
                sig = _new_func_params(smpt, sig)
            sig += ">"
    elif isinstance(parm, SuiMoveParameterType):
        sig += f"<T{str(parm.type_parameters_index)}>"
    elif isinstance(parm, SuiMoveVector):
        sig += "vector<"
        sig = _new_func_params(parm.vector_of, sig)
        sig += ">"
    elif isinstance(parm, SuiMoveScalarArgument):
        sig += parm.scalar_type
    else:
        raise AttributeError(f"Not handling {parm}")
    return sig


def _build_func_signature(func_desc: dict[str, SuiMoveFunction]) -> str:
    """_build_func_signature Builds a functions signature string.

    :param func_desc: Dictionary with func_name:func_definition
    :type func_desc: dict[str, SuiMoveFunction]
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


def print_function_signatures(mods: dict[str, SuiMoveModule], args: Namespace) -> None:
    """function_signatures Generate function signatures from package's modules.

    :param mods: Package's modules dictionary
    :type mods: dict[str, SuiMoveModule]
    :param args: Filtering criteria
    :type args: argparse.Namespace
    """
    if args.includes:
        modules = filter_modules_with_including(mods=mods, includes=args.includes, nonentries=args.nonentries)
    elif args.excludes:
        modules = filter_modules_excluding(mods=mods, excludes=args.excludes, nonentries=args.nonentries)
    else:
        modules = filter_modules_with_entry_points(mods=mods, nonentries=args.nonentries)

    # modules = _filter_functions(mods, args)
    for mod_key, mod_func_list in modules.items():
        print(f"For module {mod_key}")
        for func_hit in mod_func_list:
            print(_build_func_signature(func_hit))
