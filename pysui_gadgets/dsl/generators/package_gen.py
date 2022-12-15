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

"""pysui_gadgets: DSL Struct to Python class generator."""

import os
import shutil
import ast
import copy
from pathlib import Path
from typing import Union
from pysui_gadgets.dsl.ir.ir_types import PackageIR, ModuleIR, FunctionIR, StructIR


class StructureGen:
    """."""

    _STRUCTGEN_INIT_METHOD: str = "__init__"
    _STRUCTGEN_INSTANCE_METHOD: str = "instance"
    _STRUCTGEN_PROPERTY_METHOD: str = "_prop_stub"

    def __init__(self, *, structure_irs: list[StructIR]):
        """."""
        self.struct_irs = structure_irs

    def _get_method_for(
        self, for_method: str, ast_node: ast.ClassDef
    ) -> Union[ast.FunctionDef, ast.AsyncFunctionDef, Exception]:
        """."""
        for node in ast_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == for_method:
                    return node
        raise AttributeError(f"No method found for {for_method}")

    def update_init_node(
        self, struct_ir: StructIR, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
        """_update_init Inserts __init__ parameters and property assignments.

        :param node: The AST __init__function definition
        :type node: ast.FunctionDef
        """
        # Extend the __init__ argument list
        node.args.args.extend([ast.arg(arg=x.name, annotation=ast.Name(id=x.type_signature)) for x in struct_ir.fields])
        # Add the assignments
        node.body.extend([ast.parse(f"self.{x.name}:{x.type_signature} = {x.name}").body[0] for x in struct_ir.fields])
        return node

    def update_instance_node(
        self, struct_ir: StructIR, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
        """_update_loader Sets new struct class return type in classmethod.

        :param node: The AST get_instance classmethod function definition.
        :type node: ast.FunctionDef
        """
        node.returns = ast.Name(id=f'"{struct_ir.name}"')
        return node

    def update_property_node(
        self, struct_ir: StructIR, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> list[Union[ast.FunctionDef, ast.AsyncFunctionDef]]:
        """."""
        new_props = []
        for field in struct_ir.fields:
            if field.arg_converter_returns or field.as_arg_converter:
                as_arg_node = copy.deepcopy(node)
                as_arg_node.name = f"{field.name}_argument"
                if field.arg_converter_returns:
                    as_arg_node.returns = ast.Name(id=field.arg_converter_returns)
                if field.as_arg_converter:
                    as_arg_node.body[1] = ast.parse(f"return {field.as_arg_converter}")
                new_props.append(as_arg_node)
            if field.type_converter_returns or field.as_type_converter:
                as_type_node = copy.deepcopy(node)
                as_type_node.name = f"{field.name}_suitype"
                if field.type_converter_returns:
                    as_type_node.returns = ast.Name(id=field.type_converter_returns)
                if field.as_type_converter:
                    as_type_node.body[1] = ast.parse(f"return {field.as_type_converter}")
                new_props.append(as_type_node)
        return new_props

    def update_struct_ast(self, struct_ir: StructIR, ast_class_node: ast.ClassDef):
        """."""
        struct_init_node = self._get_method_for(self._STRUCTGEN_INIT_METHOD, ast_class_node)
        struct_instance_node = self._get_method_for(self._STRUCTGEN_INSTANCE_METHOD, ast_class_node)
        struct_property_node = self._get_method_for(self._STRUCTGEN_PROPERTY_METHOD, ast_class_node)
        prop_index = ast_class_node.body.index(struct_property_node)
        # Inline updates, ignore return
        _ = self.update_init_node(struct_ir, struct_init_node)
        # Inline updates, ignore return
        _ = self.update_instance_node(struct_ir, struct_instance_node)
        # This generates replacement property getters
        props = self.update_property_node(struct_ir, struct_property_node)
        ast_class_node.body.pop(prop_index)
        ast_class_node.body.extend(props)

    def generate(self, *, ast_node: ast.ClassDef) -> list[ast.ClassDef]:
        """."""
        new_cd_set: list[ast.ClassDef] = []
        for struct in self.struct_irs:
            new_class_def = copy.deepcopy(ast_node)
            self.update_struct_ast(struct, new_class_def)
            new_cd_set.append(new_class_def)
            new_class_def.name = struct.name
        return new_cd_set


class FunctionGen:
    """."""

    _PACKAGE_ID: str = "_package_id"
    _MODULE_ID: str = "_module_id"

    def __init__(self, *, function_irs: list[FunctionIR]):
        """."""
        self.func_irs = function_irs

    def update_init(self, *, ast_node: ast.FunctionDef, package_name: str, module_name: str):
        """."""
        package_assign = ast.parse(f"self.{self._PACKAGE_ID}: ObjectID = ObjectID('{package_name}')")
        module_assign = ast.parse(f"self.{self._MODULE_ID}: SuiString = SuiString('{module_name}')")
        ast_node.body.append(package_assign)
        ast_node.body.append(module_assign)

    def update_method(self, *, function_ir: FunctionIR, ast_node: ast.FunctionDef):
        """."""
        ast_node.name = function_ir.name
        module_assign = ast.parse(f"in_parms['package_object_id'] = self.{self._PACKAGE_ID}")
        ast_node.body.insert(2, module_assign)
        module_assign = ast.parse(f"in_parms['module'] = self.{self._MODULE_ID}")
        ast_node.body.insert(2, module_assign)
        module_assign = ast.parse(f"in_parms['function'] = SuiString('{function_ir.name}')")
        ast_node.body.insert(2, module_assign)
        # ast_node.body.append(module_assign)
        # Extend the __init__ argument list
        ast_node.args.args.extend(
            [ast.arg(arg=x.name, annotation=ast.Name(id=x.type_signature)) for x in function_ir.args]
        )

    def generate(self, *, ast_node: ast.ClassDef, package_name: str, module_name: str) -> ast.ClassDef:
        """."""
        # Update static name of class. We know the module name is lower case
        # Update the static ObjectID of the package being called
        # And we need to distinguish between a struct that may have the same name
        #

        base_func = ast_node.body.pop(-1)
        base_ident = ast_node.body.pop(-1)
        base_init = ast_node.body.pop(-1)
        self.update_init(ast_node=base_init, package_name=package_name, module_name=module_name)
        ast_node.body.append(base_init)
        ast_node.body.append(base_ident)
        for func in self.func_irs:
            func_call_ast = copy.deepcopy(base_func)
            # Change the name of the method and the str assignment
            self.update_method(function_ir=func, ast_node=func_call_ast)
            ast_node.body.append(func_call_ast)

        return ast_node


class ModuleGen:
    """."""

    def __init__(self, *, package_id: str, module_ir: ModuleIR, package_path: Path, template_path: Path):
        """."""
        self.module_path = package_path.joinpath(module_ir.name)
        self.template_path = template_path
        self.module_ir = module_ir
        self.package_id = package_id
        # Load the template
        with open(self.template_path, "rt", encoding="utf-8") as source:
            code = source.read()
        # make a generous copy
        self.module_ast: ast.Module = copy.deepcopy(ast.parse(code, type_comments=True))

    def generate(self) -> ast.Module:
        """generate Will create a module file with 'n' struct classes and 1 behavioral class."""
        if self.module_ast:
            # Get the last two classes from the template, preserv the rest
            func_ast = self.module_ast.body.pop(-1)
            struct_ast = self.module_ast.body.pop(-1)
            # Extend the list of structure classes
            struct_cds = StructureGen(structure_irs=self.module_ir.structs).generate(ast_node=struct_ast)
            # Extend the list of functions in class
            func_ast.name = self.module_ir.name.title() + "Module"
            func_cd = FunctionGen(function_irs=self.module_ir.functions).generate(
                ast_node=func_ast, package_name=self.package_id, module_name=self.module_ir.name
            )
            self.module_ast.body.extend(struct_cds)
            self.module_ast.body.append(func_cd)
        return self.module_ast


class PackageGen:
    """PacageGen creates the package layout and content."""

    def __init__(
        self, *, package_ir: PackageIR, target_path: Path, template_path: Path, overwrite_modules: bool, use_async: bool
    ):
        """__init__ Generates structure and module entry point method files.

        :param package_ir: The package/module internal representation from pysui_gadgets.dsl.ir.modir
        :type package_ir: PackageIR
        :param target_path: Path to where package/module(s) will be written to
        :type target_path: Path
        :param template_path: Path to internal templates for structs/modules
        :type template_path: Path
        :param overwrite_modules: If True, existing path/module(s) can be overwritten
        :type overwrite_modules: bool
        :param use_async: If True, an ``asynchronous`` flavor of the template(s) are used
        :type use_async: bool
        :raises ValueError: If something goes awry
        """
        self.package_ir = package_ir
        self.target_path = target_path.joinpath(package_ir.name)
        # synch vs asynch
        if use_async:
            self.template_path = template_path.joinpath("async_model.py")
        else:
            self.template_path = template_path.joinpath("sync_model.py")
        self.overwrite_modules = overwrite_modules
        # Get the reusable __init__.py for package and modules
        with open(template_path.joinpath("__init__.py"), "r", encoding="utf-8") as init_file:
            self.init_content = init_file.read()
        # Upfront testing of target state
        self.package_exists, self.modules_exist = self._check_target()
        if self.modules_exist and not self.overwrite_modules:
            raise ValueError(
                f"Modules exist for package {package_ir.name} and overwrite option = {self.overwrite_modules}"
            )

    def _check_target(self) -> tuple[bool, bool]:
        """_check_target Checks if package and modules already exist.

        :return: True or False for packcage folder and module folder respectivly
        :rtype: tuple[bool, bool]
        """
        have_package = self.target_path.exists()
        if have_package:
            mod_names = [x.name for x in self.package_ir.modules]
            filtered = list(filter(lambda x: self.target_path.joinpath(x).exists(), mod_names))
            return (have_package, len(filtered) > 0)
        return (have_package, False)

    def _write_init_py(self, base_path: Path) -> Union[None, Exception]:
        """_write_init_py Writes an ``__init__.py`` at base_path.

        :param base_path: Path to where ``__init__.py`` is written
        :type base_path: Path
        :return: Nothing or exception from file open/write
        :rtype: Union[None, Exception]
        """
        with open(base_path.joinpath("__init__.py"), "w", encoding="utf-8") as init_file:
            init_file.write(self.init_content)

    def _create_python_package(self) -> Union[None, Exception]:
        """_create_python_package Creates the initial package if not already exist.

        :return: Nothing or exception from path create or file open/write
        :rtype: Union[None, Exception]
        """
        if not self.package_exists:
            print(f"Creating package {self.package_ir.name}")
            os.mkdir(self.target_path)
            self._write_init_py(self.target_path)

    def _create_python_module(self, module_name: str, ast_node: ast.Module) -> Union[None, Exception]:
        """_create_python_module Creates a module package folder and content.

        :param module_name: Name of module (from move module)
        :type module_name: str
        :param ast_node: The python AST containing recently generated module content
        :type ast_node: ast.Module
        :return: Nothing or exception from path create or file open/writes
        :rtype: Union[None, Exception]
        """
        base_path = self.target_path.joinpath(module_name)
        base_module = base_path.joinpath(module_name + ".py")
        if base_path.exists() and self.overwrite_modules:
            shutil.rmtree(base_path)
        os.mkdir(base_path)
        with open(base_module, "w", encoding="utf-8") as module_file:
            module_file.write(ast.unparse(ast_node))
        self._write_init_py(base_path)

    def generate(self):
        """generate Generate python AST encapsulating move package/functions and struct details."""
        self._create_python_package()
        for module in self.package_ir.modules:
            mod_gen = ModuleGen(
                package_id=self.package_ir.name[1:],
                module_ir=module,
                package_path=self.target_path,
                template_path=self.template_path,
            )
            self._create_python_module(module.name, mod_gen.generate())
            # print(ast.unparse(mod_gen.generate()))
