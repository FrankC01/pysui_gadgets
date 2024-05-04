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
from pysui import SuiConfig
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn

from pysui_gadgets.utils.cmdlines import vh_parser


class ObjType(IntEnum):
    """Object type classifier."""

    COIN = 0
    OBJECT = 1
    PACKAGE = 2
    UPGRADECAP = 3
    STAKED_COIN = 4

    @classmethod
    def type_is(cls, in_type: pgql_type.ObjectReadGQL) -> "ObjType":
        """Determine classifier."""
        have_type = None
        in_type: str = in_type.object_type
        if in_type == "Package":
            have_type = ObjType.PACKAGE
        elif "sui::SUI" in in_type:
            have_type = ObjType.COIN
        elif "UpgradeCap" in in_type:
            have_type = ObjType.UPGRADECAP
        elif "StakedSui" in in_type:
            have_type = ObjType.STAKED_COIN
        else:
            have_type = ObjType.OBJECT
        return have_type


@dataclass
class ObjectState:
    """Represents an object instance associated to Object version."""

    object_ref: pgql_type.ObjectReadGQL
    tx_context: pgql_type.TransactionResultGQL

    @property
    def version(self) -> str:
        """Fetch the state object version."""
        return self.object_ref.version

    @property
    def timestamp(self) -> int:
        """Fetch the state timestamp."""
        return self.tx_context.effects["timestamp"]


class ObjectHistory:
    """Collection Class."""

    def __init__(
        self, client: SuiGQLClient, vh_type: ObjType, versions: list[ObjectState]
    ):
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

    def _scan_for_previous(
        self, target_id: str, current_txn: pgql_type.TransactionResultGQL
    ) -> Union[int, None]:
        """Find previous version if any."""
        # First check object_changes
        for changes in current_txn.effects["objectChanges"]["nodes"]:
            if "address" in changes:
                if changes["address"] == target_id:
                    if changes["created"]:
                        return None
                    if "input_state" in changes and "output_state" in changes:
                        return changes["input_state"]["version"]
        return None

    def _walk_it(self, target_id: str, current_txn: pgql_type.TransactionResultGQL):
        """Recursive walk through changes if found."""
        previous_version = self._scan_for_previous(target_id, current_txn)
        if previous_version:
            obj_read: pgql_type.ObjectReadGQL = _get_object_pv(
                self.client, target_id, previous_version
            )
            result = self.client.execute_query_node(
                with_node=qn.GetTx(digest=obj_read.previous_transaction_digest)
            )
            if result.is_ok():
                self.append_version(ObjectState(obj_read, result.result_data))
                self._walk_it(target_id, result.result_data)
            else:
                raise ValueError(result.result_string)

    def scan(self):
        """Initialize history walk."""
        base_version = self.versions[0]
        self._walk_it(base_version.object_ref.object_id, base_version.tx_context)


def _get_object_pv(
    client: SuiGQLClient, object_id: str, previous: int
) -> pgql_type.ObjectReadGQL:
    """."""
    result = client.execute_query_node(
        with_node=qn.GetPastObject(
            object_id=object_id,
            version=previous,
        )
    )

    if result.is_ok():
        if isinstance(
            result.result_data, (pgql_type.ObjectReadDeletedGQL, pgql_type.NoopGQL)
        ):
            raise ValueError(
                f"Object {object_id} does not exist or has been wrapped or deleted on chain"
            )
        return result.result_data
    else:
        raise ValueError(result.result_string)


def _get_object_now(client: SuiGQLClient, object_id: str) -> pgql_type.ObjectReadGQL:
    """."""
    result = client.execute_query_node(
        with_node=qn.GetObject(object_id=object_id.value)
    )
    if result.is_ok():
        if isinstance(
            result.result_data, (pgql_type.ObjectReadDeletedGQL, pgql_type.NoopGQL)
        ):
            raise ValueError(
                f"Object {object_id} does not exist or has been wrapped or deleted on chain"
            )
        return result.result_data
    else:
        raise ValueError(result.result_string)


def walk_history(client: SuiGQLClient, target_object_id: str) -> ObjectHistory:
    """Walk history for provided target object."""
    obj_read: pgql_type.ObjectReadGQL = _get_object_now(client, target_object_id)
    prev_tx = obj_read.previous_transaction_digest
    result = client.execute_query_node(with_node=qn.GetTx(digest=prev_tx))
    if result.is_ok():
        txn: pgql_type.TransactionResultGQL = result.result_data
        context = ObjectState(obj_read, txn)
        obj_type = ObjType.type_is(obj_read)
        vh_hist = ObjectHistory(client, obj_type, [context])
        if obj_type != ObjType.PACKAGE:
            vh_hist.scan()
        return vh_hist
    else:
        raise ValueError(result.result_string)


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

    history: list[
        Union[
            tuple[pgql_type.ObjectReadGQL, pgql_type.TransactionResultGQL],
            pgql_type.ObjectReadGQL,
            pgql_type.TransactionResultGQL,
        ]
    ]

    @classmethod
    def from_history(
        cls, history: ObjectHistory, choice: str, ascending: bool
    ) -> "ObjectContainer":
        """."""
        instance = cls.from_dict({"history": []})
        history_list = _reverse_history(history, ascending)
        match choice:
            case "all":
                instance.history = [
                    (version.object_ref, version.tx_context) for version in history_list
                ]
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
        results = [
            {"version": version.version, "timestamp_ms": version.timestamp}
            for version in history_list
        ]
        print(json.dumps(results, indent=2))
    else:
        container = ObjectContainer.from_history(history, choice, ascending)
        print(container.to_json(indent=2))


def main():
    """Main entry point."""
    arg_line = sys.argv[1:].copy()
    use_suibase = False
    # Handle a different client.yaml other than default
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        print("suibase does not support Sui GraphQL at this time.")
        arg_line = arg_line[1:]
    parsed = vh_parser(arg_line)
    if use_suibase:
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()
    # Version history
    try:
        produce_output(
            walk_history(SuiGQLClient(config=cfg), parsed.target_object),
            parsed.output,
            parsed.ascending,
        )
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
