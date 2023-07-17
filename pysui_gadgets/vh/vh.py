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

"""VH - Fetch version history of objects."""

import sys
from enum import IntEnum
from dataclasses import dataclass
from typing import Union
import json
from dataclasses_json import DataClassJsonMixin
from pysui import SuiConfig, SyncClient, handle_result
from pysui.sui.sui_builders.get_builders import GetTx
from pysui.sui.sui_txresults.single_tx import ObjectRead, ObjectNotExist
from pysui.sui.sui_txresults.complex_tx import TxResponse

from pysui_gadgets.utils.cmdlines import vh_parser


class ObjType(IntEnum):
    """Object type classifier."""

    COIN = 0
    OBJECT = 1
    PACKAGE = 2
    UPGRADECAP = 3
    STAKED_COIN = 4

    @classmethod
    def type_is(cls, in_type: ObjectRead) -> "ObjType":
        """Determine classifier."""
        have_type = None
        in_type: str = in_type.object_type
        if in_type == "package":
            have_type = ObjType.PACKAGE
        elif in_type.startswith("0x2::coin::Coin"):
            have_type = ObjType.COIN
        elif in_type == "0x2::package::UpgradeCap":
            have_type = ObjType.UPGRADECAP
        elif in_type == "0x3::staking_pool::StakedSui":
            have_type = ObjType.STAKED_COIN
        else:
            have_type = ObjType.OBJECT
        return have_type


@dataclass
class ObjectState:
    """Represents an object instance associated to Object version."""

    object_ref: ObjectRead
    tx_context: TxResponse

    @property
    def version(self) -> str:
        """Fetch the state object version."""
        return self.object_ref.version

    @property
    def timestamp(self) -> int:
        """Fetch the state timestamp."""
        return int(self.tx_context.timestamp_ms)


class ObjectHistory:
    """Collection Class."""

    def __init__(self, client: SyncClient, vh_type: ObjType, versions: list[ObjectState]):
        """Instance initializer."""
        self.client = client
        self.start_index: int = 0
        self.last_index: int = 0
        self.vh_type: ObjType = vh_type
        self.versions: list[ObjectState] = versions
        self.last_index = len(self.versions) - 1

    def append_version(self, new_state: ObjectState) -> int:
        """Add version."""
        self.versions.append(new_state)
        self.last_index += 1
        return self.last_index

    def _scan_for_previous(self, target_id: str, current_txn: TxResponse) -> Union[str, None]:
        """Find previous version if any."""
        # First check object_changes
        for changes in current_txn.object_changes:
            if "objectId" in changes:
                if changes["objectId"] == target_id:
                    if changes["type"] == "mutated":
                        return changes["previousVersion"]
        return None

    def _walk_it(self, target_id: str, current_txn: TxResponse):
        """Recursive walk through changes if found."""
        previous_version = self._scan_for_previous(target_id, current_txn)
        if previous_version:
            obj_read: ObjectRead = handle_result(self.client.get_object(target_id, int(previous_version)))
            if not isinstance(obj_read, ObjectNotExist):
                txn: TxResponse = handle_result(self.client.execute(GetTx(digest=obj_read.previous_transaction)))
                self.append_version(ObjectState(obj_read, txn))
                self._walk_it(target_id, txn)

    def scan(self):
        """Initialize history walk."""
        base_version = self.versions[0]
        self._walk_it(base_version.object_ref.object_id, base_version.tx_context)


def walk_history(client: SyncClient, target_object_id: str) -> ObjectHistory:
    """Walk history for provided target object."""
    obj_read: ObjectRead = handle_result(client.get_object(target_object_id))
    if not isinstance(obj_read, ObjectNotExist):
        prev_tx = obj_read.previous_transaction
        txn: TxResponse = handle_result(client.execute(GetTx(digest=prev_tx)))
        context = ObjectState(obj_read, txn)
        vh_hist = ObjectHistory(client, ObjType.type_is(obj_read), [context])
        vh_hist.scan()
        return vh_hist
    raise ValueError(f"Object {target_object_id} does not exist on chain")


def _reverse_history(history: ObjectHistory, ascending: bool) -> list:
    """Reverse history or return as is."""
    history_list = history.versions
    if ascending:
        start = len(history_list) - 1
        history_list = [history_list[i] for i in range(start, -1, -1)]
    return history_list


@dataclass
class ObjectContainer(DataClassJsonMixin):
    """."""

    history: list[Union[tuple[ObjectRead, TxResponse], ObjectRead, TxResponse]]

    @classmethod
    def from_history(cls, history: ObjectHistory, choice: str, ascending: bool) -> "ObjectContainer":
        """."""
        instance = cls.from_dict({"history": []})
        history_list = _reverse_history(history, ascending)
        match choice:
            case "all":
                instance.history = [(version.object_ref, version.tx_context) for version in history_list]
            case "objects":
                instance.history = [version.object_ref for version in history_list]
            case "txns":
                instance.history = [version.tx_context for version in history_list]
        return instance


def produce_output(history: ObjectHistory, choice: str, ascending: bool):
    """Generate history output."""
    results = []
    if choice == "summary":
        history_list = _reverse_history(history, ascending)
        results = [{"version": version.version, "timestamp_ms": version.timestamp} for version in history_list]
        print(json.dumps(results, indent=2))
    else:
        container = ObjectContainer.from_history(history, choice, ascending)
        print(container.to_json(indent=2))


def main():
    """Main entry point."""
    arg_line = sys.argv[1:].copy()
    use_suibase = False
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        use_suibase = True
        arg_line = arg_line[1:]
    parsed = vh_parser(arg_line)
    if use_suibase:
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()
    # Version history
    produce_output(walk_history(SyncClient(cfg), parsed.target_object), parsed.output, parsed.ascending)


if __name__ == "__main__":
    main()
