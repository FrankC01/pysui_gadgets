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

"""pysui_gadgets: DSL Generates etc., etc., etc."""

import ast
import copy
import os
import sys
from pathlib import Path
from gadgets.dsl.cmdline import build_parser
from gadgets.dsl.generators.struct_gen import StructGen
from gadgets.dsl.modir import IRBuilder
from pysui.sui import SuiClient, SuiConfig


def main():
    """Main."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    cfg_file = None
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        cfg_file = arg_line[1:2]
        arg_line = arg_line[2:]
    parsed = build_parser(arg_line)
    if cfg_file:
        cfg = SuiConfig.from_config_file(cfg_file[0])
    else:
        cfg = SuiConfig.default()

    try:
        parsed.excludes = set(parsed.excludes) if parsed.excludes else set()
        parsed.includes = set(parsed.includes) if parsed.includes else set()
        modir = IRBuilder(config=cfg, package=parsed.package_id, includes=parsed.includes, excludes=parsed.excludes)
        modir.generate_ir()
    except ValueError as valerr:
        print(f"{valerr.args}")
    # Load the struct templates
    # inpath = Path(os.path.abspath(__file__)).parent

    # template_path = inpath.joinpath("templates")
    # model_path = template_path.joinpath("model.py")
    # _class_path = template_path.joinpath("classes.py")
    # with open(model_path, "rt", encoding="utf-8") as source:
    #     code = source.read()
    # program = ast.parse(code, type_comments=True)
    # # For structs we:
    # # duplicate the classdef ast for each struct we want to create
    # #   filter program body to find classdef instance:
    # cdef = program.body.pop()
    # structs = [StructGen("First", [("one", "str"), ("two", "ObjectID"), ("three", "SuiAddress")])]
    # if cdef:
    #     cdef_list = [copy.deepcopy(cdef)]
    #     # For each class we step the structure generator
    #     index = 0
    #     while index < len(cdef_list):
    #         structs[index].build(cdef_list[index])
    #         index += 1
    #     program.body.extend(cdef_list)
    # topy = ast.unparse(program)
    # print(topy)


if __name__ == "__main__":
    main()
