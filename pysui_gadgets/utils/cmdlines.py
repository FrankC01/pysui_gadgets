#    Copyright Frank V. Castellucci
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

"""pysui-gadget: DSL package command line parser."""
import argparse

from pysui import PysuiConfiguration

from pysui_gadgets.utils.cmd_arg_validators import (
    ValidateObjectID,
    ValidateAddress,
    ValidatePackageDir,
    ValidateAlias,
    check_positive,
)


def _base_parser(pconfig: PysuiConfiguration) -> argparse.ArgumentParser:
    """Basic parser setting for all commands."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options]",
        description="",
    )
    parser.add_argument(
        "--profile",
        dest="profile_name",
        choices=pconfig.profile_names(),
        default="devnet",
        required=False,
        help="The GraphQL profile representing target GraphQL node. Default to 'devnet'",
    )
    return parser


# For to-one gadget
def to_one_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """build_parser Simple command line for app.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = _base_parser(pconfig)
    parser.description = (
        "Merges all SUI Gas mists 'to one' SUI Gas object for an address"
    )
    parser.usage = "%(prog)s [--command_options]"
    addy_arg_group = parser.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="The owner of coins to splay. Mutually exclusive with '-a'",
        action=ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of owner of coins to splay. Mutually exclusive with '-o'.",
        action=ValidateAlias,
    )
    parser.add_argument(
        "-p",
        "--primary",
        required=False,
        help="The primary coin to merge to. Defaults to first one found",
        action=ValidateObjectID,
    )
    parser.add_argument(
        "-i",
        "--inspect",
        help="Display transaction BCS structure and performs a dry run",
        required=False,
        action="store_true",
        dest="inspect",
    )

    return parser.parse_args(in_args if in_args else ["--help"])


# for package gadget
def package_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """build_parser Simple command line for app.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = _base_parser(pconfig)
    parser.description = "Display package information"
    subparser = parser.add_subparsers(title="commands", help="")

    # Simple listing of modules in package
    subp = subparser.add_parser("listmods", help="List package's modules")
    subp.add_argument(
        "-m",
        "--move-package-id",
        required=True,
        help="The move package ObjectID on the chain",
        action=ValidateObjectID,
    )
    subp.set_defaults(subcommand="listmods")

    # Generate public entry or all function signatures for one or more package modules
    subp = subparser.add_parser(
        "genfuncs", help="Generate module's function signatures"
    )
    subp.add_argument(
        "-m",
        "--move-package-id",
        required=True,
        help="The move package ObjectID on the chain",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-n",
        "--nonentry-funcs-included",
        dest="nonentries",
        required=False,
        action="store_true",
        help="Include functions that are not entry points in signature generations",
    )
    command_group = subp.add_mutually_exclusive_group()
    command_group.add_argument(
        "-e",
        "--exclude-modules",
        dest="excludes",
        required=False,
        nargs="+",
        type=str,
        help="Exclude modules from signature generation",
    )
    command_group.add_argument(
        "-i",
        "--include-modules",
        dest="includes",
        required=False,
        nargs="+",
        type=str,
        help="Only include modules for signature generation",
    )
    subp.set_defaults(subcommand="genfuncs")

    # Informational displays about a package modules structures
    subp = subparser.add_parser("genstructs", help="Show module's struct information")
    subp.add_argument(
        "-m",
        "--move-package-id",
        required=True,
        help="The move package ObjectID on the chain",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-s",
        "--short-display",
        required=False,
        dest="short_form",
        action="store_true",
        help="Print structure short form",
    )
    command_group = subp.add_mutually_exclusive_group()
    command_group.add_argument(
        "-e",
        "--exclude-modules",
        dest="excludes",
        required=False,
        nargs="+",
        type=str,
        help="Exclude modules from signature generation",
    )
    command_group.add_argument(
        "-i",
        "--include-modules",
        dest="includes",
        required=False,
        nargs="+",
        type=str,
        help="Only include modules for signature generation",
    )
    subp.set_defaults(subcommand="genstructs")

    return parser.parse_args(in_args if in_args else ["--help"])


# for splay gadget
def splay_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """splay_parser Simple command args for splay execution."""
    parser = _base_parser(pconfig)
    parser.description = "Evenly distribute gas objects across one or more addresses. Can also splay to oneself"

    addy_arg_group = parser.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="The owner of coins to splay. Mutually exclusive with '-a'",
        action=ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of owner of coins to splay. Mutually exclusive with '-o'.",
        action=ValidateAlias,
    )

    parser.add_argument(
        "-c",
        "--coins",
        dest="coins",
        required=False,
        nargs="+",
        help="The coin(s) to splay out to addresses. Defaults to all coins of owner.",
        action=ValidateObjectID,
    )
    me_parser = parser.add_mutually_exclusive_group(required=False)
    me_parser.add_argument(
        "-s",
        "--self-recipient",
        help="Splays count of coins to owner only. Mutually exclusive with '-t'",
        type=int,
        dest="self_count",
    )
    me_parser.add_argument(
        "-t",
        "--to-addresses",
        dest="addresses",
        required=False,
        nargs="+",
        help="Splay coins to addresses. Defaults to all address in configuration. Mutually exclusive with '-s'",
        action=ValidateAddress,
    )
    parser.add_argument(
        "-i",
        "--inspect",
        help="Display transaction BCS structure and performs a dry run",
        required=False,
        action="store_true",
        dest="inspect",
    )
    return parser.parse_args(in_args if in_args else ["--help"])


# for version history gadget
def vh_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """vh Simple command args for history scanning."""
    parser = _base_parser(pconfig)
    parser.description = "Discover history of object versions"

    parser.add_argument(
        "-o",
        "--object",
        dest="target_object",
        required=True,
        action=ValidateObjectID,
        help="object identifier.",
    )
    me_parser = parser.add_mutually_exclusive_group(required=True)
    me_parser.add_argument(
        "-i",
        "--for-includes",
        help="Only history when object included in transaction",
        default=False,
        action="store_true",
        dest="includes",
    )
    me_parser.add_argument(
        "-c",
        "--for-changes",
        help="Only history when object changed in transaction",
        default=False,
        action="store_true",
        dest="changes",
    )
    me_parser.add_argument(
        "-b",
        "--for-both",
        help="History for object whether included or changed in transaction",
        default=False,
        action="store_true",
        dest="both",
    )
    parser.add_argument(
        "-j",
        "--json",
        dest="output",
        choices=["all", "objects", "txns", "summary"],
        default="summary",
        help="output choices.",
    )
    parser.add_argument(
        "-a",
        "--ascending",
        help="ascending order of output",
        required=False,
        action="store_true",
        dest="ascending",
    )

    return parser.parse_args(in_args if in_args else ["--help"])
