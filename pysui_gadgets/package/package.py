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

"""pysui Package (smart contract) metadata utility.

This is a utility for inspecting the metadata of a published package on SUI.

**Short term objectives**:
* Introspection of package
* Display both entry point and module function parameter signatures
* Display type information (structs)

**Ultimate goal**:
* Generate package DSL for client side development
"""

import argparse
import sys

from typing import Union

from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_txresults import SuiMovePackage

from pysui_gadgets.package.cmdline import build_parser
from pysui_gadgets.package.cmds import lists, structs, funcs


def package(client: SuiClient, args: argparse.Namespace) -> Union[ValueError, SuiMovePackage]:
    """package Retrieve SUI move package from chain.

    :param client: Synchronous Client
    :type client: SuiClient
    :param args: Holds the address of package
    :type args: argparse.Namespace
    :raises ValueError: If error returned from client
    :return: Package's meta data
    :rtype: Union[ValueError, SuiMovePackage]
    """
    result = client.get_package(args.move_package_id)
    if result.is_ok():
        return result.result_data
    raise ValueError(f"Failed retrieving package {args.move_package_id} with return {result.result_string}")


def main() -> None:
    """Main entry point."""
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

    sui_package = package(SuiClient(cfg), parsed)
    cmd = parsed.subcommand
    vars(parsed).pop("subcommand")

    match cmd:
        case "listmods":
            lists.print_module_list(sui_package.modules, parsed)
        case "genfuncs":
            parsed.excludes = set(parsed.excludes) if parsed.excludes else set()
            parsed.includes = set(parsed.includes) if parsed.includes else set()
            funcs.print_function_signatures(sui_package.modules, parsed)
        case "genstructs":
            parsed.excludes = set(parsed.excludes) if parsed.excludes else set()
            parsed.includes = set(parsed.includes) if parsed.includes else set()
            structs.print_module_structs(sui_package.modules, parsed)


if __name__ == "__main__":
    main()
