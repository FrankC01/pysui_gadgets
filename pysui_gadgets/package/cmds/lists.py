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
from pysui.sui.sui_txresults import SuiMoveModule


def print_module_list(mods: dict[str, SuiMoveModule], args: Namespace) -> None:
    """list_mods Prints list of the SuiMovePackage modules to stdout.

    :param mods: SuiMovePackage's module dictionary
    :type package: list[str,SuiMoveModule
    """
    print(f"\nModules from package: {args.move_package_id}")
    for mod_name in mods.keys():
        print(f"\tName: {mod_name}")
