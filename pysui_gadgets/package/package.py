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

from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn

from pysui_gadgets.utils.cmdlines import package_parser
from pysui_gadgets.package.cmds import lists, structs, funcs


def package(client: SuiGQLClient, package_id: str) -> pgql_type.MovePackageGQL:
    """package Retrieve SUI move package and all it's modules from chain.

    :param client: GraphQL Client
    :type client: SuiGQLClient
    :param package_id: Holds the address of package
    :type args: str
    :raises ValueError: If error returned from client
    :return: Package's meta data
    :rtype: pgql_type.MovePackageGQL
    """
    package_modules: list[pgql_type.MoveModuleGQL] = []
    result = client.execute_query_node(with_node=qn.GetPackage(package=package_id))
    if result.is_ok():
        sui_package: pgql_type.MovePackageGQL = result.result_data
        package_modules.extend(sui_package.modules)
        while result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetPackage(
                    package=result.result_data.package_id,
                    next_page=result.result_data.next_cursor,
                )
            )
            if result.is_err():
                raise ValueError(
                    f"Failed retrieving package {package_id} with return {result.result_string}"
                )
            package_modules.extend(result.result_data.modules)
    else:
        raise ValueError(
            f"Failed retrieving package {package_id} with return {result.result_string}"
        )
    sui_package.modules = package_modules
    return sui_package


def main() -> None:
    """Main entry point."""
    arg_line = sys.argv[1:].copy()
    cfg_local = False
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        print("suibase does not support Sui GraphQL at this time.")
        arg_line = arg_line[1:]
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP  # , profile_name="testnet"
    )

    parsed = package_parser(arg_line, cfg)
    cfg.make_active(profile_name=parsed.profile_name, persist=False)
    package_id = parsed.move_package_id.value
    sui_package: pgql_type.MovePackageGQL = package(
        SuiGQLClient(pysui_config=cfg), package_id
    )
    cmd = parsed.subcommand
    vars(parsed).pop("subcommand")
    try:
        match cmd:
            case "listmods":
                lists.print_module_list(sui_package.modules, package_id)
            case "genfuncs":
                includes = set(parsed.includes) if parsed.includes else set()
                excludes = set(parsed.excludes) if parsed.excludes else set()
                funcs.print_function_signatures(
                    sui_package.modules, includes, excludes, parsed.nonentries
                )
            case "genstructs":
                parsed.excludes = set(parsed.excludes) if parsed.excludes else set()
                parsed.includes = set(parsed.includes) if parsed.includes else set()
                structs.print_module_structs(sui_package.modules, parsed)
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
