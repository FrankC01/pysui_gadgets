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
from typing import Optional
from pysui import SuiConfig, SuiAddress
from pysui_gadgets.utils.cmdlines import splay_parser
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn


def _resolve_owner(config: SuiConfig, owner, alias):
    """Resolve the parsers directive of coin ownership."""
    owner_designate: SuiAddress = None
    if owner:
        owner_designate: SuiAddress = owner
    elif alias:
        owner_designate: SuiAddress = config.addr4al(alias)
    else:
        raise ValueError(f"Owner not designated.")

    if owner_designate != config.active_address:
        if owner_designate.address not in config.addresses:
            raise ValueError(f"Missing private key for {owner_designate.address}")
        print(f"Setting coin owner to {owner_designate.address}")
        config.set_active_address(owner_designate)


def _get_all_owner_gas(client: SuiGQLClient) -> list[pgql_type.SuiCoinObjectGQL]:
    """Retreive all owners Gas Objects."""
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    owner: str = client.config.active_address.address
    result = client.execute_query_node(with_node=qn.GetCoins(owner=owner))
    while True:
        if result.is_ok():
            coin_list.extend(result.result_data.data)
            if result.result_data.next_cursor.hasNextPage:
                result = client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=owner, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"GetCoins error {result.result_string}")
    if not coin_list:
        raise ValueError(f"{owner} has no Sui coins to splay")
    return coin_list


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
        # result = txn.split_coin(coin=txn.gas, amounts=distro_balances)
        for index, target in enumerate(distro):
            txn.transfer_sui(
                from_coin=txn.gas, recipient=target, amount=distro_balances[index]
            )
            # txn.transfer_sui(recipient=target, from_coin=result[index])


def _inspect(
    client: SuiGQLClient, txn: SuiTransaction, target_gas=pgql_type.SuiCoinObjectGQL
):
    """."""
    print(txn.raw_kind().to_json(indent=2))
    tx_bytes = txn.build(use_gas_objects=[target_gas])
    result = client.execute_query_node(
        with_node=qn.DryRunTransaction(tx_bytestr=tx_bytes)
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        raise ValueError(f"Error in dry run {result.result_string}")


def _execute(
    client: SuiGQLClient, txn: SuiTransaction, target_gas=pgql_type.SuiCoinObjectGQL
):
    """."""
    tx_b64, sig_array = txn.build_and_sign(use_gas_objects=[target_gas])
    result = client.execute_query_node(
        with_node=qn.ExecuteTransaction(tx_bytestr=tx_b64, sig_array=sig_array)
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        raise ValueError(f"Error in dry run {result.result_string}")


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
    print(parsed)
    if cfg_file:
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()

    try:
        _resolve_owner(cfg, parsed.owner, parsed.alias)
        sui_client = SuiGQLClient(config=cfg)
        all_gas = _get_all_owner_gas(sui_client)
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
            _inspect(sui_client, transaction, target_gas)
        else:
            _execute(sui_client, transaction, target_gas)

    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
