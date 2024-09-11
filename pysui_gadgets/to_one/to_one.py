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

"""pysui_gadgets: Collapse two or more coints for address."""


import sys
from typing import Optional

from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui_gadgets.utils.exec_helpers as utils
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui_gadgets.utils.cmdlines import to_one_parser


def _to_one_coin(
    client: SuiGQLClient,
    coins: list[pgql_type.SuiCoinObjectGQL],
    primary_coin: Optional[str],
) -> tuple[pgql_type.SuiCoinObjectGQL, SuiTransaction]:
    """Setup consolidation of coins in play."""

    target_gas: pgql_type.SuiCoinObjectGQL = None
    # If primary coin, remove from coin list
    if primary_coin:
        p_pos: int = -1
        for index, coin in enumerate(coins):
            if primary_coin == coin.object_id:
                p_pos = index
                target_gas = coin
                coins.remove(target_gas)
                break
        if p_pos < 0:
            raise ValueError(
                f"Primary coin {primary_coin} not found in owner's gas coins"
            )
    else:
        target_gas = coins[0]
        coins = coins[1:]

    # Merge all remaining coins to gas
    # preserving the target gas coint
    txn = SuiTransaction(client=client)
    txn.merge_coins(merge_to=txn.gas, merge_from=coins)
    return (
        target_gas,
        txn,
    )


def main():
    """Main entry point."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    if arg_line and arg_line[0] == "--local":
        print("suibase does not support Sui GraphQL at this time.")
        arg_line = arg_line[1:]
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP  # , profile_name="testnet"
    )

    parsed = to_one_parser(arg_line, cfg)
    cfg.make_active(profile_name=parsed.profile_name, persist=False)

    try:
        utils.util_resolve_owner(cfg, parsed.owner, parsed.alias)
        sui_client = SuiGQLClient(pysui_config=cfg)
        all_gas = utils.util_get_all_owner_gas(sui_client, cfg.active_address)
        if len(all_gas) == 1:
            raise ValueError("to-one requires the owner has more than 1 gas coin.")

        target_gas, transaction = _to_one_coin(
            sui_client, all_gas, (parsed.primary.value if parsed.primary else None)
        )
        if parsed.inspect:
            utils.util_inspect(sui_client, transaction, target_gas)
        else:
            utils.util_execute(sui_client, transaction, target_gas)

    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
