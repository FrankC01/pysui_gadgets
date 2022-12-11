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

import ast


class StructGen:
    """Structure to Class generation.

    Used to generate equivalent move struct in python.

    It's builder is called with a templated ClassDef AST node and the
    objective is to:

    #. decorate the ``__init__`` function with one specific to the move struct.
    #. decorate the ``get_instance`` function with the return type of new classname.

    Because this is a classdef from our template, we know the ``__init__`` function is
    offset 1 in the body
    """

    _STRUCTGEN_INIT: str = "__init__"
    _STRUCTGEN_CLASSMETHOD: str = "get_instance"

    def __init__(self, struct_name: str, args: list[tuple[str, str]]) -> None:
        """Initialize with changes."""
        self.struct_name = struct_name
        self.init_args: list[tuple[str, str]] = args

    def build(self, node: ast.ClassDef):
        """build Geneerate the data class aligned to move module struct.

        :param node: The input templatized AST class node
        :type node: ast.ClassDef
        """

        def _update_init(node: ast.FunctionDef):
            """_update_init Inserts __init__ parameters and property assignments.

            :param node: The AST __init__function definition
            :type node: ast.FunctionDef
            """
            node.args.args.extend([ast.arg(arg=x, annotation=ast.Name(id=y)) for x, y in self.init_args])
            node.body.extend([ast.parse(f"self.{x}:{y} = {x}").body[0] for x, y in self.init_args])

        def _update_loader(node: ast.FunctionDef):
            """_update_loader Sets new struct class return type in classmethod.

            :param node: The AST get_instance classmethod function definition.
            :type node: ast.FunctionDef
            """
            node.returns = ast.Name(id=self.struct_name)

        node.name = self.struct_name
        # Standard in template is the __init__ function is before
        # all other functions
        func_nodes = list(filter(lambda x: isinstance(x, ast.FunctionDef), node.body))
        if (
            func_nodes
            and len(func_nodes) >= 2
            and func_nodes[0].name == self._STRUCTGEN_INIT
            and func_nodes[1].name == self._STRUCTGEN_CLASSMETHOD
        ):
            _update_init(func_nodes[0])
            _update_loader(func_nodes[1])
        else:
            raise ValueError("Unable to locate class function definitions")
