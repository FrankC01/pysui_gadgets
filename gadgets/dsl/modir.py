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

"""pysui_gadgets: DSL - Module Interpreter."""


import os
from pathlib import Path
from typing import Any, Iterator, Union
from dataclasses import dataclass, field

from pysui.sui import SuiConfig, SuiClient
from pysui.sui.sui_types import (
    ObjectID,
    SuiPackage,
    SuiMoveField,
    SuiParameterStruct,
    SuiParameterReference,
    SuiMoveParameterType,
    SuiMoveScalarArgument,
    SuiMoveVector,
)

from gadgets.utils import filters


@dataclass
class FieldIR:
    """."""

    name: str
    type_signature: str


@dataclass
class StructIR:
    """."""

    name: str
    fields: list[FieldIR] = field(default_factory=list)


@dataclass
class FunctionIR:
    """."""

    name: str
    args: list[FieldIR] = field(default_factory=list)


@dataclass
class ModuleIR:
    """."""

    name: str
    structs: list[StructIR] = field(default_factory=list)
    functions: list[FunctionIR] = field(default_factory=list)

    def structure_for(self, struct_name: str) -> Union[None, StructIR, Exception]:
        """."""
        finder = list(filter(lambda x: x.name == struct_name, self.structs))
        if finder:
            if len(finder) == 1:
                return finder[0]
            raise AttributeError(f"{struct_name} exists more than once in {self.name}")
        return None


@dataclass
class PackageIR:
    """."""

    name: str
    modules: list[ModuleIR] = field(default_factory=list)

    def module_for(self, module_name: str) -> Union[None, ModuleIR, Exception]:
        """."""
        finder = list(filter(lambda x: x.name == module_name, self.modules))
        if finder:
            if len(finder) == 1:
                return finder[0]
            raise AttributeError(f"{module_name} exists more than once in {self.name}")
        return None


class Package:
    """."""

    TEMPLATE_PATH: Path = Path(os.path.abspath(__file__)).parent.joinpath("templates")
    MODEL_PATH = TEMPLATE_PATH.joinpath("model.py")
    CLASS_PATH = TEMPLATE_PATH.joinpath("classes.py")

    def __init__(self, package_id: ObjectID, package: SuiPackage):
        """Initializer."""
        self.package = package
        self.package_data = PackageIR("_" + package_id.value, [])

    def _find_or_create_module_for(self, module_name: str) -> ModuleIR:
        """."""
        found = self.package_data.module_for(module_name)
        if not found:
            result = ModuleIR(module_name, [], [])
            self.package_data.modules.append(result)
        else:
            result = found
        return result

    def add_function(self, module_name: str, class_ir: FunctionIR) -> "Package":
        """."""
        # Find module
        mod_ir = self._find_or_create_module_for(module_name)
        mod_ir.functions.append(class_ir)
        return self

    def add_struct(self, module_name: str, struct_ir: StructIR) -> "Package":
        """."""
        # Find module
        mod_ir = self._find_or_create_module_for(module_name)
        mod_ir.structs.append(struct_ir)
        return self

    def has_struct(self, module_name: str, struct_name: str) -> Union[StructIR, None]:
        """."""
        mod_ir = self.package_data.module_for(module_name)
        if mod_ir:
            return mod_ir.structure_for(struct_name)
        return None


class IRBuilder:
    """Retrieves and builds structure and operational intermediate representation.

    Information is retrieved for getting the SUI package meta data and then
    iterating through the various artifacts to generalize both structure and function
    information relevant to generating Python DSL for module(s)
    """

    def __init__(
        self, *, config: SuiConfig, package: ObjectID, includes: list[str] = None, excludes: list[str] = None
    ) -> None:
        """__init__ Initialize the IR interpreter with SUI package metadata.

        :param config: The SUI configuration in use
        :type config: SuiConfig
        :param package: The package identifier
        :type package: ObjectID
        :param includes: List of module names to only include in generation of DSL, defaults to None
        :type includes: list[str], optional
        :param excludes: List of module names to exclude from generation of DSL, defaults to None
        :type excludes: list[str], optional
        :raises ValueError: If error interfacing with SUI blockchain
        """
        self.client: SuiClient = SuiClient(config)
        self.includes = includes
        self.excludes = excludes
        getp_result = self.client.get_package(package_id=package)
        if getp_result.is_ok():
            self.package_ir = Package(package, getp_result.result_data)
        else:
            raise ValueError(f"Getting package {package.value} error {getp_result.result_string}")

    def _field_type_signature(self, field_ref: SuiMoveField, field_str: str = "") -> str:
        """."""

        def _field_type(ftype: Any, in_str: str) -> str:
            if isinstance(ftype, str):
                match ftype:
                    case "U8" | "U16" | "U32" | "U64" | "U128" | "U256":
                        in_str += "int"
                    case "Bool":
                        in_str += "bool"
                    case "Address":
                        in_str += "SuiAddress"
                    case _:
                        in_str += f"Don't know {ftype}"
            elif isinstance(ftype, SuiParameterStruct):
                if ftype.name == "UID":
                    in_str += "ObjectID"
                elif ftype.name == "String":
                    in_str += "str"
                else:
                    in_str += "Any"
                # in_str += f"{ftype.name} (see {ftype.address}::{ftype.module})"
            elif isinstance(ftype, SuiMoveVector):
                in_str += "list["
                in_str = _field_type(ftype.vector_of, in_str)
                in_str += "]"
            elif isinstance(ftype, SuiMoveParameterType):
                in_str += "ObjectID"
            else:
                in_str += f" figuring it out {type(ftype)}"
            return in_str

        field_str += _field_type(field_ref.type_, "")
        return field_str

    def _struct_ir(self, module_name: str, key_structs: Iterator):
        """."""
        for struct_name, struct_def in key_structs:
            fields = [FieldIR(field.name, self._field_type_signature(field)) for field in struct_def.fields]
            self.package_ir.add_struct(module_name, StructIR(struct_name, fields))

    def _func_sig(self, mod_ir: ModuleIR, field_type: Any) -> str:
        """."""
        if isinstance(field_type, SuiParameterStruct):
            if mod_ir.structure_for(field_type.name):
                arg_str = field_type.name
            else:
                arg_str = "ObjectID"
        elif isinstance(field_type, SuiParameterReference):
            arg_str = self._func_sig(mod_ir, field_type.reference_to)
        elif isinstance(field_type, SuiMoveScalarArgument):
            match field_type.scalar_type:
                case "U8" | "U16" | "U32" | "U64" | "U128" | "U256":
                    arg_str = "SuiInteger"
                # case "Bool":
                #     in_str += "bool"
                case "Address":
                    arg_str = "SuiAddress"
                case _:
                    arg_str = f"Don't know {field_type.scalar_type}"

        else:
            arg_str = f"No IDEA {field_type}"

        return arg_str

    def _func_ir(self, module_name: str, functions: Iterator):
        """."""
        mod_ir = self.package_ir.package_data.module_for(module_name)
        for func_name, func_def in functions:
            field_index = 0
            field_list = []
            for parm in func_def.parameters:
                field_list.append(FieldIR(f"arg_{field_index}", self._func_sig(mod_ir, parm)))
                field_index += 1
            self.package_ir.add_function(module_name, FunctionIR(func_name, field_list))

    def generate_ir(self) -> bool:
        """generate_ir Generates modules structs and classes.

        :return: True if successful
        :rtype: bool
        """
        modules = self.package_ir.package.modules
        if self.includes:
            modules = filters.filter_include_modules(mods=modules, includes=self.includes)
        elif self.excludes:
            modules = filters.filter_modules_excluding(mods=modules, excludes=self.excludes)

        # Only get modules whose functions contain at least 1 entry point function
        modules = list(filter(filters.mod_with_entry_points, modules.items()))
        # We want all Key StructIR with FieldIRs
        # Getting those first so that function args may reference by ir struct class
        for mod_name, mod_def in modules:
            self._struct_ir(mod_name, filters.filter_key_structs(mod_def.structs))
        # We want all entry point only FunctionIR with FieldIRs
        for mod_name, mod_def in modules:
            self._func_ir(mod_name, filters.filter_entry_points(mod_def))
        print(self.package_ir.package_data)
        return True
