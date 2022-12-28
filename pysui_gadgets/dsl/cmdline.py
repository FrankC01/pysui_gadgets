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

"""pysui-gadget: DSL package command line parser."""
import argparse

from pysui_gadgets.utils.cmd_arg_validators import ValidateObjectID


def build_parser(in_args: list) -> argparse.Namespace:
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
