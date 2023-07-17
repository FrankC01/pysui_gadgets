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

"""pysui_gadgets: Module deserialize and analyze *.mv files."""

import sys
from pathlib import Path
from typing import get_type_hints
from pysui import SuiConfig, SyncClient, ObjectID
from pysui.sui.sui_utils import publish_build, CompiledPackage
from pysui.sui.sui_builders.get_builders import GetObject
from pysui.sui_move.module.deserialize import from_base64, RawModuleContent
from pysui_gadgets.utils.cmdlines import module_parser


def _project_to_base64(project_path: Path) -> list[str]:
    """_project_to_base64 Returns base64 encoded base module.

    :param project_path: Path to the sui move project folder
    :type project_path: Path
    :return: The base64 encoded string of the core module of project
    :rtype: str
    """
    package: CompiledPackage = publish_build(project_path)
    return [x.value for x in package.compiled_modules]


def _address_to_base64(package_object: ObjectID, config: SuiConfig) -> list[str]:
    """_address_to_base64 Returns base64 encoded base module.

    :param package_object: The package object id on chain.
    :type package_object: ObjectID
    :param config: The SuiConfig being used
    :type config: SuiConfig
    :raises ValueError: If getting raw object from chain fails
    :return: _description_
    :return: The base64 encoded string of the core module of project
    :rtype: str
    """
    client = SyncClient(config)
    result = client.execute(GetObject(object_id=package_object, options=GetObject.package_options()))
    if result.is_ok():
        if hasattr(result.result_data.bcs, "module_map"):
            obj_data = result.result_data.bcs.module_map
            return list(obj_data.values())
        raise ValueError(f"ObjectID {package_object.value} is not a valid package")
    raise ValueError(f"{result.result_string}")


class Module:
    """."""

    def __init__(self, raw_tables: RawModuleContent, mod_index: int):
        """."""
        _handle = raw_tables.module_handles[mod_index]
        self.name = raw_tables.identifiers[_handle.identifier_index].identifier
        self.package_address = raw_tables.addresses[_handle.address_index].address

    def __repr__(self):
        """."""
        return f"Module(name:'{self.name}', package_address:{self.package_address})"


def tables_summary(raw_tables: RawModuleContent):
    """."""
    for field_name, _field_type in get_type_hints(raw_tables).items():
        infield = getattr(raw_tables, field_name)
        if isinstance(infield, list):
            print(f"Table: '{field_name}' entries = {len(infield)}")
        else:
            print(f"Field: '{field_name}' = {infield}")


def resolve_modules(raw_tables: RawModuleContent) -> list[Module]:
    """."""
    return [Module(raw_tables, mod_index) for mod_index in range(len(raw_tables.module_handles))]


def _deserialize(modules_b64: list[str]) -> list[RawModuleContent]:
    """."""
    # return [from_base64(x) for x in modules_b64]
    mod_tables: list[RawModuleContent] = [from_base64(x) for x in modules_b64]
    for mtable in mod_tables:
        print(Module(mtable, 0))
    for mtable in mod_tables:
        tables_summary(mtable)
        print()
        for mod in resolve_modules(mtable):
            print(mod)


def main():
    """main Entry point."""
    arg_line = sys.argv[1:].copy()
    cfg_file = False
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        cfg_file = True
        arg_line = arg_line[1:]

    parsed = module_parser(arg_line)
    print(parsed)
    if parsed.prj_folder:
        print(f"Fetching from {parsed.prj_folder}")
        b64_str = _project_to_base64(parsed.prj_folder)
    elif parsed.chn_package:
        if cfg_file:
            cfg = SuiConfig.sui_base_config()
        else:
            cfg = SuiConfig.default_config()
        print(f"Fetching from {parsed.chn_package.value}")
        b64_str = _address_to_base64(parsed.chn_package, cfg)
    _deserialize(b64_str)


if __name__ == "__main__":
    main()
