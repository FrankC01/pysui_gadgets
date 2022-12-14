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

"""pysui: DSL IR Types."""

from dataclasses import dataclass, field
from typing import Union


@dataclass
class FieldIR:
    """Represents a field and it's pysui or python type.

    Used for both structs and functions.
    """

    name: str = field(default_factory=str)
    type_signature: str = field(default_factory=str)
    meta: str = field(default_factory=str)
    as_arg_converter: str = field(default_factory=str)
    arg_converter_returns: str = field(default_factory=str)
    as_type_converter: str = field(default_factory=str)
    type_converter_returns: str = field(default_factory=str)


@dataclass
class StructIR:
    """Represents an IR from SUI struct to python class.

    It has a name and it's fields for the python class generation.
    """

    name: str
    fields: list[FieldIR] = field(default_factory=list)


@dataclass
class FunctionIR:
    """Represents a IR from SUI entry point methods to python methods.

    It has a name and it's fields for the python method signature generation.

    """

    name: str
    args: list[FieldIR] = field(default_factory=list)


@dataclass
class ModuleIR:
    """Represents a IR from SUI module.

    It has a name and it contains zero or more functions and struct IRs.
    Functions are constrained to only those that are entry points in the module.
    Structs are constraint to only those that have a ``has key...` ability.
    """

    name: str
    structs: list[StructIR] = field(default_factory=list)
    functions: list[FunctionIR] = field(default_factory=list)

    def structure_for(self, struct_name: str) -> Union[None, StructIR, Exception]:
        """."""
        finder = list(filter(lambda x: x.name == struct_name, self.structs))
        if finder:
            if len(finder) == 1:
                return finder[0]
            raise AttributeError(f"{struct_name} exists more than once in {self.name}")
        return None


@dataclass
class PackageIR:
    """Represents a IR from SUI package.

    It has a name and contains zero or more modules.
    """

    name: str
    modules: list[ModuleIR] = field(default_factory=list)

    def module_for(self, module_name: str) -> Union[None, ModuleIR, Exception]:
        """."""
        finder = list(filter(lambda x: x.name == module_name, self.modules))
        if finder:
            if len(finder) == 1:
                return finder[0]
            raise AttributeError(f"{module_name} exists more than once in {self.name}")
        return None
