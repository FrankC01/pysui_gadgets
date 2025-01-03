#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui-gadget: module, struct and function general utilities.

Provides low level filtering options of raw return of modules, structs and functions.
"""

import functools
from typing import Iterator
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_txresults.package_meta import (
    SuiMoveFunction,
    SuiMoveModule,
    SuiMoveStruct,
)

_MODULE_TUPLE_NAME_POS: int = 0
_MODULE_TUPLE_FUNC_POS: int = 1
_MODULE_TUPLE_MODULE_POS: int = 1


# Predicates
def module_name_is(include_list: list[str], mods: pgql_type.MoveModuleGQL) -> bool:
    """."""
    return mods.module_name in include_list


def module_name_not(exclude_list: list[str], mods: pgql_type.MoveModuleGQL) -> bool:
    """."""
    return mods.module_name not in exclude_list


def all_functions(funcs: tuple[str, SuiMoveFunction]) -> bool:
    """."""
    return True


def entry_functions_only(funcs: tuple[str, SuiMoveFunction]) -> bool:
    """."""
    return funcs[_MODULE_TUPLE_FUNC_POS].is_entry


def mod_with_entry_points(mods: tuple[str, SuiMoveModule]) -> bool:
    """."""
    return list(
        (
            filter(
                entry_functions_only,
                mods[_MODULE_TUPLE_MODULE_POS].exposed_functions.items(),
            )
        )
    )


def struct_abilities_with(
    abilities: set[str], structs: tuple[str, SuiMoveStruct]
) -> bool:
    """."""
    return abilities.intersection(structs[1].abilities.abilities)


def filter_key_structs(structs: dict[str, SuiMoveStruct]) -> Iterator:
    """."""
    return filter(functools.partial(struct_abilities_with, {"Key"}), structs.items())


def filter_entry_points(module: SuiMoveModule) -> Iterator:
    """."""
    return filter(entry_functions_only, module.exposed_functions.items())


def filter_modules_with_entry_points(
    *, mods: dict[str, pgql_type.MoveModuleGQL], nonentries: bool = False
) -> dict[str, list[dict[str, SuiMoveFunction]]]:
    """filter_entry_points Produces a list of functions found, and grouped, for one or more modules.

    :param mods: Dictionary of move modules
    :type mods: dict[str, pgql_type.MoveModuleGQL]
    :param nonentries: Include both non-entry/non-public entry point functions for the module, defaults to False
    :type nonentries: bool, optional
    :return: A module key dictionary containing a function name key and function value dictionary
    :rtype: dict[str, list[dict[str, SuiMoveFunction]]]
    """
    # Find functions that are at least entry points or we are including non-entry points as well
    result_dict = {}
    for mod_name, mod_def in mods.items():
        func_list = []
        if mod_def.module_functions:
            for func in mod_def.module_functions.functions:
                if (func.is_entry or func.visibility == "PUBLIC") or nonentries:
                    func_list.append({func.function_name: func})
            if func_list:
                result_dict[mod_name] = func_list
    return result_dict


def filter_include_modules(
    *, mods: list[pgql_type.MoveModuleGQL], includes: list[str]
) -> list[pgql_type.MoveModuleGQL]:
    """filter_include_modules Returns modules whose names are in the includes list.

    :param mods: SuiMovePackage modules dictionary
    :type mods: dict[str, SuiMoveModule]
    :param includes: List of module names to use in filter
    :type includes: list[str]
    :return: list of module_name:MoveModuleGQL that passed the includes critieria
    :rtype: list[pgql_type.MoveModuleGQL]
    """
    # filter any includes only
    return list(filter(functools.partial(module_name_is, includes), mods))


def filter_exclude_modules(
    *, mods: dict[str, SuiMoveModule], excludes: list[str]
) -> dict[str, SuiMoveModule]:
    """filter_exclude_modules Returns modules whose names are not in the excludes list.

    :param mods: SuiMovePackage modules dictionary
    :type mods: dict[str, SuiMoveModule]
    :param includes: List of module names to use in filter
    :type includes: list[str]
    :return: Dictionary of module_name:SuiMoveModule that passed the excludes critieria
    :rtype: dict[str, SuiMoveModule]
    """
    # filter any includes only
    return dict(filter(functools.partial(module_name_not, excludes), mods.items()))


def filter_modules_with_including(
    *,
    mods: dict[str, pgql_type.MoveModuleGQL],
    includes: list[str] = None,
    nonentries: bool = False,
) -> dict[str, list[dict[str, SuiMoveFunction]]]:
    """filter_modules_with_including Produces a list of functions found, and grouped, for one or more modules.

    An ``includes`` list will cherry pick only modules with matching names.

    :param mods: Dictionary of move modules
    :type mods: dict[str, SuiMoveModule]
    :param includes: list of module names to include in the result
    :type includes: list[str]
    :param nonentries: Include both non-entry point and entry point functions for the module
    :type nonentries: bool
    :return: A module key dictionary containing a function name key and function value dictionary
    :rtype: dict[str, list[dict[str, SuiMoveFunction]]]
    """
    # filter any includes only
    return filter_modules_with_entry_points(
        mods=filter_include_modules(mods=mods, includes=includes), nonentries=nonentries
    )


def filter_modules_excluding(
    *,
    mods: dict[str, SuiMoveModule],
    excludes: list[str] = None,
    nonentries: bool = False,
) -> dict[str, list[dict[str, SuiMoveFunction]]]:
    """filter_modules_excluding Produces a list of functions found, and grouped, for one or more modules.

    An ``includes`` list will ignore modules with matching names.

    :param mods: Dictionary of move modules
    :type mods: dict[str, SuiMoveModule]
    :param excludes: list of module names to exclude from the result
    :type excludes: list[str]
    :param nonentries: Include both non-entry point and entry point functions for the module
    :type nonentries: bool
    :return: A module key dictionary containing a function name key and function value dictionary
    :rtype: dict[str, list[dict[str, SuiMoveFunction]]]
    """
    # filter out any excludes
    return filter_modules_with_entry_points(
        mods=filter_exclude_modules(mods=mods, excludes=excludes), nonentries=nonentries
    )
