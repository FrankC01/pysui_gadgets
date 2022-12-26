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

"""DSL Generator init."""

from typing import Any
from pysui.sui.sui_types.scalars import (
    ObjectID,
    SuiString,
    SuiInteger,
    SuiBoolean,
)
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.address import SuiAddress


def pass_through(indata: Any) -> Any:
    """."""
    return indata


def to_object_id(indata: str) -> ObjectID:
    """."""
    return ObjectID(indata)


def to_sui_boolean(indata: str) -> SuiBoolean:
    """."""
    return SuiBoolean(indata)


def bool_sui_boolean(indata: bool) -> SuiBoolean:
    """."""
    return SuiBoolean(indata)


def to_sui_string(indata: str) -> SuiString:
    """."""
    return SuiString(indata)


def to_sui_string_array(indata: list) -> SuiArray:
    """."""
    if indata:
        for item in indata:
            if isinstance(item, list):
                raise AttributeError(f"Don't know converting inner array {indata}")
        res = SuiArray([SuiString(x) for x in indata])
    else:
        res = SuiArray([])
    return res


def to_sui_integer(indata: str) -> SuiInteger:
    """."""
    return SuiInteger(int(indata))


def to_sui_address(indata: str) -> SuiAddress:
    """."""
    return SuiAddress.from_hex_string(indata)
