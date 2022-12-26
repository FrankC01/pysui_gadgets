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


from typing import Any, Iterator, Union

from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_types.scalars import ObjectID
from pysui.sui.sui_txresults.single_tx import SuiPackage
from pysui.sui.sui_txresults.package_meta import (
    SuiMoveField,
    SuiParameterStruct,
    SuiParameterReference,
    SuiMoveScalarArgument,
    SuiMoveVector,
)

from pysui_gadgets.utils import filters
from pysui_gadgets.dsl.ir.ir_types import PackageIR, ModuleIR, FunctionIR, StructIR, FieldIR


class Package:
    """."""

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

    def _struct_field_type(self, field_ref: SuiMoveField) -> FieldIR:
        """."""

        def _field_type(ftype: Any, field_ir: FieldIR) -> str:
            type_name = type(ftype).__name__
            match type_name:
                case "str":
                    field_ir.meta = ftype
                    match ftype:
                        case "U8" | "U16" | "U32" | "U64" | "U128" | "U256":
                            field_ir.type_signature = "str"
                            field_ir.as_arg_converter = f"converter.to_sui_string(self.{field_ir.name})"
                            field_ir.arg_converter_returns = "SuiString"
                            field_ir.as_type_converter = f"converter.to_sui_integer(self.{field_ir.name})"
                            field_ir.type_converter_returns = "SuiInteger"
                        case "Bool":
                            field_ir.type_signature = "bool"
                            field_ir.as_arg_converter = f"converter.bool_sui_boolean(self.{field_ir.name})"
                            field_ir.arg_converter_returns = "SuiBoolean"
                            field_ir.as_type_converter = f"converter.bool_sui_boolean(self.{field_ir.name})"
                            field_ir.type_converter_returns = "SuiBoolean"
                        case "Address":
                            field_ir.type_signature = "str"
                            field_ir.as_arg_converter = f"converter.to_sui_address(self.{field_ir.name})"
                            field_ir.arg_converter_returns = "SuiAddress"
                            field_ir.as_type_converter = f"converter.to_sui_address(self.{field_ir.name})"
                            field_ir.type_converter_returns = "SuiAddress"
                        case _:
                            # field_ir.type_signature = "str"
                            # field_ir.as_arg_converter = f"converter.to_sui_string(self.{field_ir.name})"
                            raise AttributeError(f"Unable to service {ftype}")
                case "SuiParameterStruct":
                    field_ir.meta = ftype.name
                    field_ir.type_signature = "str"
                    if field_ir.name == "id" and ftype.name == "UID":
                        field_ir.as_arg_converter = f"converter.to_sui_string(self.{field_ir.name})"
                        field_ir.arg_converter_returns = "SuiString"
                        field_ir.as_type_converter = f"converter.to_object_id(self.{field_ir.name})"
                        field_ir.type_converter_returns = "ObjectID"
                case "SuiMoveVector":
                    field_ir.type_signature = "list["
                    inner = _field_type(ftype.vector_of, FieldIR(name="spare"))
                    field_ir.type_signature += inner.type_signature
                    field_ir.type_signature += "]"
                    field_ir.meta = f"vector[{inner.meta}]"
                    field_ir.as_arg_converter = f"converter.to_sui_string_array(self.{field_ir.name})"
                    field_ir.arg_converter_returns = "SuiArray"
                    field_ir.as_type_converter = f"converter.to_sui_string_array(self.{field_ir.name})"
                    field_ir.type_converter_returns = "SuiArray"
                case "SuiMoveParameterType":
                    field_ir.meta = ftype.name
                    field_ir.type_signature = "str"
                    field_ir.as_arg_converter = f"converter.to_sui_string(self.{field_ir.name})"
                    field_ir.as_type_converter = f"converter.to_object_id(self.{field_ir.name})"
                case _:
                    raise AttributeError(f" Can't figure  it out {type(ftype)}")
            return field_ir

        field_ir = FieldIR(name=field_ref.name)
        return _field_type(field_ref.type_, field_ir=field_ir)

    def _struct_ir(self, module_name: str, key_structs: Iterator):
        """."""
        for struct_name, struct_def in key_structs:
            fields = [self._struct_field_type(field) for field in struct_def.fields]
            self.package_ir.add_struct(module_name, StructIR(struct_name, fields))

    def _func_sig(self, mod_ir: ModuleIR, field_type: Any) -> str:
        """."""
        if isinstance(field_type, SuiParameterStruct):
            if field_type.name == "TxContext":
                return None
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
        elif isinstance(field_type, SuiMoveVector):
            arg_str = "SuiArray"
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
                asig = self._func_sig(mod_ir, parm)
                if asig:
                    field_list.append(FieldIR(f"arg_{field_index}", asig))
                    field_index += 1
            self.package_ir.add_function(module_name, FunctionIR(func_name, field_list))

    def generate_ir(self) -> PackageIR:
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
        # print(self.package_ir.package_data)
        return self.package_ir.package_data
