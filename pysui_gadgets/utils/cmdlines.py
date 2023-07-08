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

from pysui_gadgets.utils.cmd_arg_validators import ValidateObjectID, ValidateAddress, ValidatePackageDir, check_positive

# For dsl gadget
def dsl_parser(in_args: list) -> argparse.Namespace:
    """build_parser Simple command line for app.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(add_help=True, usage="%(prog)s [--command_options]")

    parser.add_argument(
        "-m",
        "--move-package-id",
        dest="package_id",
        required=True,
        help="The move package ObjectID on the chain",
        action=ValidateObjectID,
    )
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument(
        "-e",
        "--exclude-modules",
        dest="excludes",
        required=False,
        nargs="+",
        type=str,
        help="Exclude modules from DL generation",
    )
    command_group.add_argument(
        "-i",
        "--include-modules",
        dest="includes",
        required=False,
        nargs="+",
        type=str,
        help="Only include modules for DSL generation",
    )

    parser.add_argument(
        "-p",
        "--generation-root-path",
        dest="root_path",
        required=True,
        help="Identify root path to generate package and modules to",
    )

    parser.add_argument(
        "-o",
        "--overwrite-target-files",
        dest="overwrite_modules",
        required=False,
        action="store_true",
        help="Overwrite existing files during generation",
    )
    parser.add_argument(
        "-a",
        "--generate-async",
        dest="use_async",
        required=False,
        action="store_true",
        help="Generate async module otherwise default to synchrounous",
    )
    return parser.parse_args(in_args if in_args else ["--help"])


# For to-one gadget
def to_one_parser(in_args: list) -> argparse.Namespace:
    """build_parser Simple command line for app.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [--command_options]",
        description="Merges all SUI Gas mists 'to one' SUI Gas object for an address",
    )
    parser.add_argument(
        "-a", "--address", required=True, help="The address whose SUI coin to converge to one", action=ValidateAddress
    )
    parser.add_argument(
        "-p",
        "--primary",
        required=False,
        help="The primary coin to merge to. Defaults to first one found",
        action=ValidateObjectID,
    )
    parser.add_argument(
        "-m",
        "--merge-threshold",
        required=False,
        default=10,
        help="Sets the number of coins to merge at a time. Defaults to 10.",
        type=check_positive,
    )
    return parser.parse_args(in_args if in_args else ["--help"])


# for package gadget
def package_parser(in_args: list) -> argparse.Namespace:
    """build_parser Simple command line for app.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(add_help=True, usage="%(prog)s command [--command_options]")

    subparser = parser.add_subparsers(title="commands", help="")

    # Simple listing of modules in package
    subp = subparser.add_parser("listmods", help="List package's modules")
    subp.add_argument(
        "-m", "--move-package-id", required=True, help="The move package ObjectID on the chain", action=ValidateObjectID
    )
    subp.set_defaults(subcommand="listmods")

    # Generate public entry or all function signatures for one or more package modules
    subp = subparser.add_parser("genfuncs", help="Generate module's function signatures")
    subp.add_argument(
        "-m", "--move-package-id", required=True, help="The move package ObjectID on the chain", action=ValidateObjectID
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
        "-m", "--move-package-id", required=True, help="The move package ObjectID on the chain", action=ValidateObjectID
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


# for module gadget
def module_parser(in_args: list) -> argparse.Namespace:
    """module_parser Simple command line for module execution.

    :param in_args: list of argument strings
    :type in_args: list
    :return: Parse results
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [--command_options]",
        description="Deserialize and analyze Sui module byte-codes",
    )
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument(
        "-p",
        "--package-project",
        dest="prj_folder",
        required=False,
        action=ValidatePackageDir,
        # type=str,
        help="Ingest modules from sui move project folder",
    )
    command_group.add_argument(
        "-a",
        "--package-address",
        dest="chn_package",
        required=False,
        action=ValidateObjectID,
        help="Ingest modules from chain package address",
    )

    return parser.parse_args(in_args if in_args else ["--help"])


# for splay gadget
def splay_parser(in_args: list) -> argparse.Namespace:
    """splay_parser Simple command args for splay execution."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [--command_options]",
        description="Evenly distribute gas objects across zero (self) or more addresses",
    )
    parser.add_argument(
        "-o",
        "--owner",
        dest="owner",
        required=True,
        action=ValidateAddress,
        help="The owner of coins to splay",
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
        "-a", "--address-owner", help="splays coins to owner only for count", type=int, dest="self_count"
    )
    me_parser.add_argument(
        "-t",
        "--to-address",
        dest="addresses",
        required=False,
        nargs="+",
        help="splay coins to addresses.",
        action=ValidateAddress,
    )
    parser.add_argument(
        "-m",
        "--merge-threshold",
        dest="threshold",
        required=False,
        default=10,
        help="Sets the number of coins to merge at a time. Defaults to 10.",
        type=check_positive,
    )
    parser.add_argument(
        "-i", "--inspect", help="inspect and do not execute", required=False, action="store_true", dest="inspect"
    )
    return parser.parse_args(in_args if in_args else ["--help"])


# for version history gadget
def vh_parser(in_args: list) -> argparse.Namespace:
    """vh Simple command args for history scanning."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [--command_options]",
        description="Discover history of object versions",
    )
    parser.add_argument(
        "-o",
        "--object",
        dest="target_object",
        required=True,
        action=ValidateObjectID,
        help="object identifier.",
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
        "-a", "--ascending", help="ascending order of output", required=False, action="store_true", dest="ascending"
    )

    return parser.parse_args(in_args if in_args else ["--help"])
