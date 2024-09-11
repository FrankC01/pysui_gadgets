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

"""List commands and utilities."""

from argparse import Namespace
from typing import Any
from pysui.sui.sui_txresults.package_meta import (
    SuiMoveField,
    SuiMoveModule,
    SuiMoveStructTypeParameter,
    SuiParameterStruct,
    SuiMoveVector,
    SuiMoveParameterType,
)

from pysui_gadgets.utils import filters


def _struct_parm_types(holder: list, sig: str) -> str:
    """."""
    if holder:
        sig += f"has {', '.join(holder)}"
    return sig


def _struct_parm_abilities(holder: list[str], sig: str) -> str:
    """."""
    accum = []
    tindex = 0
    found = False
    accum = [x for x in holder]
    if accum:
        sig = f"<{','.join(accum)}> "
    return sig


def _field_signature(field: SuiMoveField, field_str: str) -> str:
    """."""

    def _field_type(ftype: Any, in_str: str) -> str:
        if isinstance(ftype, str):
            in_str += ftype
        elif isinstance(ftype, SuiParameterStruct):
            in_str += f"{ftype.name} (see {ftype.address}::{ftype.module})"
        elif isinstance(ftype, SuiMoveVector):
            in_str += "vector<"
            in_str = _field_type(ftype.vector_of, in_str)
            in_str += ">"
        elif isinstance(ftype, SuiMoveParameterType):
            in_str += f"<T{ftype.type_parameters_index}>"
        else:
            in_str += f" figuring it out {type(ftype)}"
        return in_str

    field_str += _field_type(field.field_type, "")
    return field_str


def print_module_structs(modules: dict[str, SuiMoveModule], args: Namespace) -> None:
    """."""
    if args.includes:
        modules = filters.filter_include_modules(mods=modules, includes=args.includes)
    elif args.excludes:
        modules = filters.filter_modules_excluding(mods=modules, excludes=args.excludes)

    for mod_def in modules:
        print(f"\nModule {mod_def.module_name}")
        for struct_def in mod_def.module_structures.structures:
            sig = _struct_parm_abilities(struct_def.abilities, "")
            # sig += _struct_parm_types(struct_def.abilities.abilities, "")
            print(f"\nStruct: {struct_def.struct_name} {sig} {{")
            max_field_name = max([len(x["field_name"]) for x in struct_def.fields])
            if not args.short_form:
                for field in struct_def.fields:
                    print(field)
            else:
                for field in struct_def.fields:
                    print(
                        f"    {field.name:{max_field_name}s}: {_field_signature(field,'')}"
                    )
            print("}")
