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

import os
import sys
from pathlib import Path
from pysui.sui.sui_config import SuiConfig
from pysui_gadgets.dsl.cmdline import build_parser
from pysui_gadgets.dsl.ir.modir import IRBuilder
from pysui_gadgets.dsl.generators.package_gen import PackageGen

_TEMPLATE_PATH: Path = Path(os.path.abspath(__file__)).parent.joinpath("templates")
# _MODEL_PATH = _TEMPLATE_PATH.joinpath("sync_model.py")


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
    # print(parsed)
    try:
        parsed.excludes = set(parsed.excludes) if parsed.excludes else set()
        parsed.includes = set(parsed.includes) if parsed.includes else set()
        ir_builder = IRBuilder(
            config=cfg, package=parsed.package_id, includes=parsed.includes, excludes=parsed.excludes
        )
        package_gen = PackageGen(
            package_ir=ir_builder.generate_ir(),
            target_path=Path(parsed.root_path),
            template_path=_TEMPLATE_PATH,
            overwrite_modules=parsed.overwrite_modules,
            use_async=parsed.use_async,
        )
        package_gen.generate()

    except AttributeError as atterr:
        print(f"{atterr.args}")
    except ValueError as valerr:
        print(f"{valerr.args}")


if __name__ == "__main__":
    main()
