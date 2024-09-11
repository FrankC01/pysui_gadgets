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
from functools import reduce
import json
from dataclasses_json import DataClassJsonMixin
from pysui import PysuiConfiguration
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


def _get_all_txns(
    client: SuiGQLClient,
    object_id: str,
    includes: bool,
    changes: bool,
    both: bool,
) -> list[pgql_type.TransactionSummaryGQL]:
    """Retrieves all previous versions of object_id."""
    history_filter: dict[str, str] = {}
    if includes:
        history_filter["inputObject"] = object_id
    elif changes:
        history_filter["changedObject"] = object_id
    elif both:
        history_filter["inputObject"] = object_id
        history_filter["changedObject"] = object_id

    result = client.execute_query_node(
        with_node=qn.GetFilteredTx(tx_filter=history_filter)
    )
    tx_list: list[pgql_type.TransactionSummaryGQL] = []
    while result.is_ok():
        txs: pgql_type.TransactionSummariesGQL = result.result_data
        tx_list.extend(txs.data)
        if txs.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetFilteredTx(
                    tx_filter=history_filter, next_page=txs.next_cursor
                )
            )
        else:
            break
    if result.is_err():
        raise ValueError(result.result_string)
    return tx_list


def _get_object_now(client: SuiGQLClient, object_id: str) -> pgql_type.ObjectReadGQL:
    """Retrieves current state object by object_id."""
    result = client.execute_query_node(with_node=qn.GetObject(object_id=object_id))
    if result.is_ok():
        if isinstance(
            result.result_data, (pgql_type.ObjectReadDeletedGQL, pgql_type.NoopGQL)
        ):
            raise ValueError(
                f"Object '{object_id}' does not exist, is has been wrapped or has been deleted."
            )
        return result.result_data
    else:
        raise ValueError(result.result_string)


def _get_transaction(
    client: SuiGQLClient, digest: str
) -> pgql_type.TransactionResultGQL:
    """Retrieves transaction details for digest."""
    result = client.execute_query_node(with_node=qn.GetTx(digest=digest))
    if result.is_ok():
        return result.result_data
    raise ValueError(result.result_string)


@dataclass
class History:
    client: SuiGQLClient
    object_id: str
    object_type: ObjType
    object_states: list[ObjectState]


def _walker(accum: History, value: pgql_type.TransactionSummaryGQL):
    """."""
    # Get the summary detailed transaction
    current_tx = _get_transaction(accum.client, value.digest)
    for changes in current_tx.effects["objectChanges"]["nodes"]:
        if "address" in changes:
            if changes["address"] == accum.object_id:
                if changes["created"]:
                    pass
                if "input_state" in changes and "output_state" in changes:
                    accum.object_states.append(
                        ObjectState(
                            _get_object_pv(
                                accum.client,
                                accum.object_id,
                                changes["input_state"]["version"],
                            ),
                            current_tx,
                        )
                    )

    # Get the previous version to fetch the object at said state
    return accum


def walk_history(
    client: SuiGQLClient,
    target_object_id: str,
    includes: bool,
    changes: bool,
    both: bool,
) -> History:
    """Walk history for provided target object."""
    obj_read: pgql_type.ObjectReadGQL = _get_object_now(client, target_object_id)
    all_txns: list[pgql_type.TransactionSummaryGQL] = _get_all_txns(
        client, target_object_id, includes, changes, both
    )
    result_states: History = None
    if all_txns:
        # Reverse list to descending order
        all_txns.reverse()
        # Get base type
        obj_states: list[ObjectState] = [
            ObjectState(obj_read, _get_transaction(client, all_txns[0].digest))
        ]
        result_states: History = reduce(
            _walker,
            all_txns,
            History(
                client,
                target_object_id,
                ObjType.type_is(obj_read),
                obj_states,
            ),
        )
    return result_states


def _reverse_history(history: History, ascending: bool) -> list:
    """Reverse history or return as is."""
    history_list = history.object_states
    if ascending:
        history_list.reverse()
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


def produce_output(history: History, choice: str, ascending: bool):
    """Generate history output."""
    results = []
    if choice == "summary":
        history_list = _reverse_history(history, ascending)
        results = [
            {
                "version": version.version,
                "timestamp_ms": version.timestamp,
                "content": version.object_ref.content,
            }
            for version in history_list
        ]
        print(json.dumps(results, indent=2))
    else:
        container = ObjectContainer.from_history(history, choice, ascending)
        print(container.to_json(indent=2))


def main():
    """Main entry point."""
    arg_line = sys.argv[1:].copy()
    if arg_line and arg_line[0] == "--local":
        print("suibase does not support Sui GraphQL at this time.")
        arg_line = arg_line[1:]
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP  # , profile_name="testnet"
    )
    parsed = vh_parser(arg_line, cfg)
    cfg.make_active(profile_name=parsed.profile_name, persist=False)
    # Version history
    try:
        produce_output(
            walk_history(
                SuiGQLClient(pysui_config=cfg),
                parsed.target_object.value,
                parsed.includes,
                parsed.changes,
                parsed.both,
            ),
            parsed.output,
            parsed.ascending,
        )
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
