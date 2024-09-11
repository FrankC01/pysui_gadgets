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

import pysui.sui.sui_pgql.pgql_types as pgql_type


def print_module_list(mods: list[pgql_type.MoveModuleGQL], package_id: str) -> None:
    """list_mods Prints list of the SuiMovePackage modules to stdout.

    :param mods: List of package modules
    :type package: list[pgql_type.MoveModuleGQL]
    """
    print(f"\nModules from package: {package_id}")
    for mmodule in mods:
        print(f"\tName: {mmodule.module_name}")
