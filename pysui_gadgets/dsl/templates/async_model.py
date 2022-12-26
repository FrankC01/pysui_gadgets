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

"""pysui-gadget DSL Template.

Copyright Frank V. Castellucci

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from abc import ABC
from pysui.sui.sui_types.scalars import *
from pysui.sui.sui_types.collections import *
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_clients import async_client
from pysui.sui.sui_builders.exec_builders import MoveCall
from pysui.sui.sui_txresults.single_tx import ObjectRead
from pysui_gadgets.dsl.dsl_run import converter


class _Inner(ABC):
    """Base abstraction."""

    _MOVE_CALL_CONST_SET = {
        "signer",
        "package_object_id",
        "module",
        "function",
        "gas",
        "gas_budget",
    }

    def __init__(self):
        """Initialize."""

    def type_args(self, args: dict) -> SuiArray:
        """."""
        my_types = list(
            filter(
                lambda x: isinstance(x, _Inner) and not isinstance(x.type_arg, SuiNullType),
                args.values(),
            )
        )
        if my_types:
            return [x.type_arg for x in my_types]
        return my_types

    def to_call_args(self, in_params: dict) -> dict:
        """Convert raw argument dictionary to segregate arguments for move call parms."""
        in_args = {x: y for (x, y) in in_params.items() if x in self._MOVE_CALL_CONST_SET}
        not_in_args = {x: y for (x, y) in in_params.items() if x not in self._MOVE_CALL_CONST_SET}
        final_args = []
        for (_arg_name, arg_value) in not_in_args.items():
            if isinstance(arg_value, _Inner):
                final_args.append(getattr(arg_value, "id_argument"))
            elif issubclass(arg_value.__class__, SuiScalarType):
                final_args.append(SuiString(arg_value.value))
        in_args["arguments"] = final_args
        in_args["type_arguments"] = self.type_args(not_in_args)
        return in_args


class _StructStub(_Inner):
    """Generated from pysui-dsl StructIRs."""

    _INIT_FROM_CLASS: bool = False

    def __init__(self, type_arg: SuiString):
        """Initialize class object fields."""
        if not self._INIT_FROM_CLASS:
            raise RuntimeError("Init can only be called from get_instance classmethod.")
        super().__init__()
        self.type_arg = type_arg

    @classmethod
    async def instance(cls, from_details: ObjectRead):
        """Class instantiation from module struct details."""
        cls._INIT_FROM_CLASS = True
        if hasattr(from_details.data, "type_arg") and from_details.data.type_arg:
            type_arg = SuiString(from_details.data.type_arg)
        else:
            type_arg = SuiNullType()
        instance = cls(type_arg, **from_details.data.fields)
        cls._INIT_FROM_CLASS = False
        return instance

    @property
    def _prop_stub(self):
        """Read property generated."""
        return None


class _ModuleStub(_Inner):
    """Generated from pysui-dsl modules FunctionIR entries."""

    def __init__(self, client: async_client.SuiClient):
        """Initialize."""
        super().__init__()
        self.client: async_client.SuiClient = client

    @property
    def identifier(self) -> SuiString:
        """Returns module identifier."""
        return getattr(self, "module_id")

    async def _mod_func_call(self, signer: SuiAddress, gas: ObjectID, gas_budget: SuiInteger) -> SuiRpcResult:
        """Generated from module entry point functions."""
        in_parms = locals().copy()
        in_parms.pop("self")
        return await self.client.execute(MoveCall(**self.to_call_args(in_parms)))
