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
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.common import handle_result
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_clients.transaction import SuiTransaction
from pysui.sui.sui_types.scalars import ObjectID
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types import bcs
from pysui.sui.sui_txresults.single_tx import SuiCoinObjects
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult, TxResponse

from pysui_gadgets.utils.cmdlines import splay_parser


def _set_sender(txn: SuiTransaction, owner: SuiAddress) -> SuiTransaction:
    """Assign the transaction owner."""
    txn.signer_block.sender = owner or txn.client.config.active_address
    return txn


def _coin_merge(txn: SuiTransaction, coins: list[ObjectID]):
    """Coin merge as defined or all for owner."""
    merge_required = True
    a_coins: list[SuiCoinObjects] = handle_result(txn.client.get_gas(txn.signer_block.sender.address)).data
    to_coin = txn.gas
    from_coins = a_coins[1:]
    a_coin_set = {x.coin_object_id for x in a_coins}
    # If there are explict coins, validate they are part of owners gas then setup to/from
    if coins:
        i_coin_set = {x.value for x in coins}
        if i_coin_set.issubset(a_coin_set):
            a_coins = handle_result(txn.client.get_objects_for(coins))
            to_coin = a_coins[0]
            if len(coins) == 1:
                merge_required = False
            else:
                from_coins = a_coins[1:]
        else:
            raise ValueError(f"Invalid coin ID found in set {i_coin_set}")
    else:
        if len(a_coins) == 1:
            merge_required = False

    if merge_required:
        txn.merge_coins(merge_to=to_coin, merge_from=from_coins)


def _splay_out(txn: SuiTransaction, same_address: int, addresses: list[SuiAddress]):
    """Perform the distribution of rolled up coins."""
    distribute_required = True
    bcs_res: list[bcs.Argument] = []
    # Distribute rollup to self based on same_address
    if same_address:
        distribute_required = False
        txn.split_coin_equal(coin=txn.gas, split_count=same_address)
    # Distribute rollup to addresses identified
    elif addresses:
        bcs_res = txn.split_coin_and_return(coin=txn.gas, split_count=len(addresses) + 1)
    # Distribute rollup to addresses owned by this configuration
    else:
        sender_addy = txn.signer_block.sender.address
        addresses = [SuiAddress(x) for x in txn.client.config.addresses if x != sender_addy]
        bcs_res = txn.split_coin_and_return(coin=txn.gas, split_count=len(addresses) + 1)

    if distribute_required and bcs_res:
        for index, res in enumerate(bcs_res):
            txn.transfer_objects(transfers=res, recipient=addresses[index])


def _inspect_only(txn: SuiTransaction):
    """Run the inspection of the splay transaction.."""
    print(txn.raw_kind().to_json(indent=2))
    inspect_result: TxInspectionResult = txn.inspect_all()
    if inspect_result and inspect_result.effects.status.succeeded:
        print(f"Gas total: {inspect_result.effects.gas_used.total}", end="")
        print(f" after rebate: {inspect_result.effects.gas_used.total_after_rebate}")
        print(inspect_result.to_json(indent=2))
    elif not inspect_result.effects.status.succeeded:
        print(f"Inspection execution failed: {inspect_result.effects.status.error}")
    else:
        print(f"Inspection failed: {inspect_result.result_string}")


def _execute(txn: SuiTransaction):
    """Execute the transaction."""
    tx_result: TxResponse = handle_result(txn.execute(gas_budget="100000"))
    if tx_result.effects.status.succeeded:
        print(tx_result.to_json(indent=2))
    else:
        print(f"Inspection execution failed: {tx_result.effects.status.error}")


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
    # Prepare transaction and Identify the owner of coins being splayed as well as who signs
    txn = _set_sender(SuiTransaction(SuiClient(cfg)), parsed.owner)
    # Merge any/all coins
    _coin_merge(txn, parsed.coins)
    # Distribute merged coins equally to any/all addresses
    _splay_out(txn, parsed.self_count, parsed.addresses)
    if parsed.inspect:
        _inspect_only(txn)
    else:
        _execute(txn)


if __name__ == "__main__":
    main()
