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


from abc import ABC, abstractmethod
from typing import Any
from pysui import version
from pysui.sui.sui_types import ObjectRead, ObjectID, SuiAddress, SuiString, SuiArray, SuiInteger
from pysui.sui.sui_rpc import SuiClient, SuiRpcResult
from pysui.sui.sui_builders import MoveCall
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

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Return an identifier of class."""

    def type_args(self, args: dict) -> SuiArray:
        """."""
        my_types = list(
            filter(lambda x: isinstance(x, _Inner) and hasattr(x, "type_arg") and getattr(x, "type_arg"), args.values())
        )
        if my_types:
            return [x.data.type_arg for x in my_types]
        return SuiArray(my_types)

    def to_call_args(self, in_params: dict) -> dict:
        """Convert raw argument dictionary to segregate arguments for move call parms."""
        # Start with static MoveCall builder parms
        in_args = {x: y for x, y in in_params.items() if x in self._MOVE_CALL_CONST_SET}
        not_in_args = {x: y for x, y in in_params.items() if x not in self._MOVE_CALL_CONST_SET}
        final_args = []
        for arg_name, arg_value in not_in_args.items():
            final_args.append(getattr(arg_value, f"{arg_name}_argument"))
        in_args["arguments"] = final_args
        in_args["type_arguments"] = self.type_args(not_in_args)
        return in_args


class _StructStub(_Inner):
    """Generated from pysui-dsl StructIRs."""

    _INIT_FROM_CLASS: bool = False

    def __init__(self, type_arg: SuiString):
        """Initialize."""
        if not self._INIT_FROM_CLASS:
            raise RuntimeError("Init can only be called from get_instance classmethod.")
        super().__init__()
        self.type_arg = type_arg

    @classmethod
    def instance(cls, from_details: ObjectRead):
        """Class thing."""
        cls._INIT_FROM_CLASS = True
        if from_details.data.type_arg:
            type_arg = SuiString(from_details.data.type_arg)
        else:
            type_arg = SuiString("")
        # 0.3.0 workaround
        if version.__version__ == "0.3.0":
            from_details.data.fields["id"] = from_details.data.fields["id"]["id"]
        else:
            from_details.data.fields["id"] = from_details.data.fields["id"]

        instance = cls(type_arg, **from_details.data.fields)
        cls._INIT_FROM_CLASS = False
        return instance

    @property
    def _prop_stub(self) -> Any:
        return None


class _ModuleStub(_Inner):
    """Generated from pysui-dsl modules FunctionIR entries."""

    def __init__(self, client: SuiClient):
        """Initialize."""
        super().__init__()
        self.client = client

    @property
    def identifier(self) -> SuiString:
        return getattr(self, "module_id")

    def _mod_func_call(self, signer: SuiAddress, gas: ObjectID, gas_budget: SuiInteger) -> SuiRpcResult:
        """."""
        in_parms = locals()
        in_parms.pop("self")
        return self.client.execute(MoveCall(**self.to_call_args(in_parms)))
