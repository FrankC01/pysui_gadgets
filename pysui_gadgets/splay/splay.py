#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


"""Splay - Splits coins evenly across addresses."""

import sys
import base64
from typing import Optional
from pysui import PysuiConfiguration
from pysui_gadgets.utils.cmdlines import splay_parser
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui_gadgets.utils.exec_helpers as utils
import pysui.sui.sui_pgql.pgql_types as pgql_type


def _consolidate_coin(
    client: SuiGQLClient,
    coins: list[pgql_type.SuiCoinObjectGQL],
    coin_ids: Optional[list[str]],
) -> tuple[pgql_type.SuiCoinObjectGQL, SuiTransaction, int]:
    """Setup consolidation of coins in play."""

    from_coins = coins
    # If not coin_ids, all user coins are in play
    if coin_ids:
        if len(coin_ids) > len(coins):
            raise ValueError(
                f"Count of targeted coins {len(coin_ids)} exceeds available coins {len(coins)}"
            )
        # Get object ids only into a set
        coin_ids_set = {x.value for x in coin_ids}
        # Get actual coins in set
        coin_set = {x.object_id for x in coins}
        # Make sure they are valid
        not_found = coin_ids_set.difference(coin_set)
        if not_found:
            raise ValueError(f"Targeted coins {not_found} do not exist in owners coins")
        from_coins = [x for x in coins if x.object_id in coin_ids_set]

    txn = SuiTransaction(client=client)
    # Get total balance for distribution
    total_balance: int = 0
    for scoin in from_coins:
        total_balance += int(scoin.balance)
    # If more than 1 coin in play, merge all others to it
    if len(from_coins) > 1:
        txn.merge_coins(merge_to=txn.gas, merge_from=from_coins[1:])
    # Regardless, coin 0 is the targeted gas coin for splitting
    return from_coins[0], txn, total_balance


def _split_and_distribute_coins(
    txn: SuiTransaction, addresses: list, total_balance: int
):
    """Distribute the coins to other addresses."""

    distro = [x for x in addresses if x != txn.client.config.active_address.address]
    if distro:
        distro = list(set(distro))
        dlen = len(distro)
        partial_balance = int(total_balance / (dlen if dlen > 1 else 2))
        distro_balances = [partial_balance for x in distro]
        result = txn.split_coin(coin=txn.gas, amounts=distro_balances)
        for index, target in enumerate(distro):
            txn.transfer_objects(transfers=[result[index]], recipient=target)


def main():
    """Main entry point."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        print("suibase does not support Sui GraphQL at this time.")
        arg_line = arg_line[1:]
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP  # , profile_name="testnet"
    )
    parsed = splay_parser(arg_line, cfg)
    cfg.make_active(profile_name=parsed.profile_name, persist=False)

    try:
        utils.util_resolve_owner(cfg, parsed.owner, parsed.alias)
        sui_client = SuiGQLClient(pysui_config=cfg)
        all_gas = utils.util_get_all_owner_gas(sui_client, cfg.active_address)
        target_gas, transaction, total_balance = _consolidate_coin(
            sui_client, all_gas, parsed.coins
        )
        if parsed.self_count:
            transaction.split_coin_equal(
                coin=transaction.gas, split_count=parsed.self_count
            )
        else:
            use_addresses = cfg.addresses
            if parsed.addresses:
                use_addresses = [x.address for x in parsed.addresses]
            _split_and_distribute_coins(transaction, use_addresses, total_balance)
        if parsed.inspect:
            utils.util_inspect(sui_client, transaction, target_gas)
        else:
            utils.util_execute(sui_client, transaction, target_gas)

    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
