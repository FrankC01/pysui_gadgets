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

"""pysui-gadget: package command line parser."""
import argparse

from pysui_gadgets.utils.cmd_arg_validators import ValidateObjectID


def build_parser(in_args: list) -> argparse.Namespace:
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
