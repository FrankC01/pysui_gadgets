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

"""pysui-gadget: To-One package command line parser."""

import argparse

from pysui_gadgets.utils.cmd_arg_validators import ValidateObjectID, ValidateAddress


def build_parser(in_args: list) -> argparse.Namespace:
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
    return parser.parse_args(in_args if in_args else ["--help"])
