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

"""Splay - Splits coins evenly across addresses."""

import sys
from typing import Callable, Optional, Union
from pysui import SyncClient, SuiConfig, ObjectID, SuiAddress, handle_result, SuiRpcResult
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_types import bcs
from pysui.sui.sui_utils import partition
from pysui.sui.sui_txresults.single_tx import SuiCoinObjects, SuiCoinObject
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult

from pysui_gadgets.utils.cmdlines import splay_parser
from pysui_gadgets.utils.exec_helpers import add_owner_to_gas_object

# Maximum coin inputs to merge to balance cost


def _inspect_only(txn: SyncTransaction, gas_id: Optional[str] = None):
    """Run the inspection of the splay transaction.."""
    print(txn.raw_kind().to_json(indent=2))
    inspect_result = txn.inspect_all()
    if isinstance(inspect_result, SuiRpcResult):
        return inspect_result
    if isinstance(inspect_result, TxInspectionResult):
        return SuiRpcResult(True, "", inspect_result)


def _execute(txn: SyncTransaction, gas_id: Optional[str] = None):
    """Execute the transaction."""
    return txn.execute(use_gas_object=gas_id)


def _set_sender(txn: SyncTransaction, owner: SuiAddress) -> SyncTransaction:
    """Assign the transaction owner."""
    txn.signer_block.sender = owner or txn.client.config.active_address
    return txn


def _validate_owned_coins(all_coins: list[SuiCoinObjects], use_coins: list[ObjectID]) -> list[SuiCoinObjects]:
    """."""
    a_coin_ids = [x.object_id for x in all_coins]
    result_coins: list[SuiCoinObjects] = []
    for coin in use_coins:
        try:
            idx = a_coin_ids.index(coin.value)
            result_coins.append(all_coins[idx])
        except ValueError as ive:
            raise ValueError(f"Coin: {coin.value} is not one of owners gas objects") from ive

    return result_coins


def _coin_merge(
    client: SyncClient,
    owner: SuiAddress,
    coins: list[ObjectID],
    threshold: int,
    call_fn: Callable[[SyncTransaction, Optional[str]], SuiRpcResult],
) -> Union[SuiCoinObject, SuiRpcResult]:
    """Coin merge as defined or all for owner."""
    merge_required = True
    clean_owner = owner.address
    a_coins: list[SuiCoinObjects] = handle_result(client.get_gas(clean_owner, True)).data

    # If there are explict coins, validate they are part of owners gas then setup to/from
    if coins:
        result_coins = _validate_owned_coins(a_coins, coins)
        if len(result_coins) == 1:
            to_coin = add_owner_to_gas_object(clean_owner, result_coins[0])
            merge_required = False
        else:
            result_coins = [add_owner_to_gas_object(clean_owner, x) for x in result_coins]
            to_coin = result_coins[0]
            from_coins = result_coins[1:]
    else:
        if len(a_coins) == 1:
            merge_required = False
            to_coin = add_owner_to_gas_object(clean_owner, a_coins[0])
        else:
            result_coins = [add_owner_to_gas_object(clean_owner, x) for x in a_coins]
            to_coin = result_coins[0]
            from_coins = result_coins[1:]

    if merge_required:
        print(f"Merging {len(from_coins)} coins to {to_coin.object_id}")
        if len(from_coins) <= threshold:

            txn = SyncTransaction(client, initial_sender=owner)
            _ = txn.merge_coins(merge_to=txn.gas, merge_from=from_coins)
            res = call_fn(txn, to_coin.object_id)
            if not res.is_ok():
                print("Failure on coin merge")
                return res
        else:
            converted = 0
            for chunk in list(partition(from_coins, threshold)):
                txn = SyncTransaction(client, initial_sender=owner)
                _ = txn.merge_coins(merge_to=txn.gas, merge_from=chunk)
                res = call_fn(txn, to_coin.object_id)
                if res.is_ok():
                    converted += len(chunk)
                else:
                    print(f"Failure on coin in range {converted} -> {res.result_string}")
                    return res
    return to_coin


def _splay_out(
    client: SyncClient,
    owner: SuiAddress,
    primary: SuiCoinObject,
    same_address: int,
    addresses: list[SuiAddress],
    call_fn: Callable[[SyncTransaction, Optional[str]], SuiRpcResult],
) -> SuiRpcResult:
    """."""
    distribute_required = True
    bcs_res: list[bcs.Argument] = []
    # Distribute rollup to self based on same_address
    txn = SyncTransaction(client, initial_sender=owner)
    # If splaying to self
    if same_address:
        distribute_required = False
        txn.split_coin_equal(coin=txn.gas, split_count=same_address)
        result = call_fn(txn, primary.object_id)
    # Or splaying to others
    elif addresses:
        bcs_res = txn.split_coin_and_return(coin=txn.gas, split_count=len(addresses) + 1)
    # Or splaying to all addresses known to configuration
    else:
        sender_addy = txn.signer_block.sender.address
        addresses = [SuiAddress(x) for x in client.config.addresses if x != sender_addy]
        bcs_res = txn.split_coin_and_return(coin=txn.gas, split_count=len(addresses) + 1)
    if distribute_required and bcs_res:
        for index, res in enumerate(bcs_res):
            txn.transfer_objects(transfers=res, recipient=addresses[index])
        result = call_fn(txn, primary.object_id)

    return result


def main():
    """Main entry point."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    cfg_file = False
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        cfg_file = True
        arg_line = arg_line[1:]
    parsed = splay_parser(arg_line)
    if cfg_file:
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()
    # Setyup client
    client = SyncClient(cfg)
    # Merge any/all coins
    primary = _coin_merge(
        client, parsed.owner, parsed.coins, parsed.threshold, _inspect_only if parsed.inspect else _execute
    )
    if isinstance(primary, SuiRpcResult):
        print(f"Failed {primary.result_string}")
    else:
        print(f"Ready to splay {primary.object_id}")
        res = _splay_out(
            client,
            parsed.owner,
            primary,
            parsed.self_count,
            parsed.addresses,
            _inspect_only if parsed.inspect else _execute,
        )
        if isinstance(res, SuiRpcResult):
            if res.is_ok():
                print(res.result_data.to_json(indent=2))
            else:
                print(res.result_string)


if __name__ == "__main__":
    main()
