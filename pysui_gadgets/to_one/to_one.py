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

"""pysui_gadgets: To One main module."""


import sys
import argparse
from pysui.sui.sui_types.scalars import SuiString, SuiInteger, ObjectID
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_clients import sync_client
from pysui.sui.sui_builders.get_builders import GetCoinTypeBalance, GetCoins
from pysui.sui.sui_builders.exec_builders import PayAllSui
from pysui_gadgets.to_one.cmdline import build_parser


def _get_gas(client: sync_client.SuiClient, address: SuiAddress) -> SuiRpcResult:
    """Efficient enumeration of SUI coins."""
    coin_type = SuiString("0x2::sui::SUI")
    result = client.execute(GetCoinTypeBalance(owner=address, coin_type=coin_type))
    if result.is_ok():
        limit = SuiInteger(result.result_data.items[0].coin_object_count)
        result = client.execute(GetCoins(owner=address, coin_type=coin_type, limit=limit))
    return result


def _join_coins(client: sync_client.SuiClient, args: argparse.Namespace):
    """Using PayAllSui builder, join all mists from all gas object to one for an address."""
    gas_res = _get_gas(client, args.address)
    if gas_res.is_ok():
        # Collect the OIDs of the coins, validate more than 2
        just_oids = [ObjectID(x.coin_object_id) for x in gas_res.result_data.data]
        if len(just_oids) < 2:
            print("Can't join with less than 2 coins")
            return
        # Primary coin 0 is the coin all merge to
        primary = args.primary if args.primary else just_oids[0]
        # Ensure that the primary is the first in the list of objects
        primary_index = just_oids.index(primary)
        if primary_index != 0:
            just_oids.insert(0, just_oids.pop(primary_index))
        # Show the user whats going on
        print("\nConsolidating all coins for address to Primary")
        for coid in just_oids:
            if primary == coid:
                print(f"{coid} <- Primary")
                continue
            print(coid)
        # Merge 'em all
        pay_res = client.execute(
            PayAllSui(signer=args.address, input_coins=just_oids, recipient=args.address, gas_budget=SuiInteger(1000))
        )
        if pay_res.is_ok():
            # Validate 1 coin left and show it's attributes
            post_gas_res = _get_gas(client, args.address)
            if post_gas_res.is_ok() and len(post_gas_res.result_data.data) == 1:
                print("Coin merge success. Result:")
                print(post_gas_res.result_data.data[0].to_json(indent=2))
            else:
                print("Result error")
        else:
            print("Transaction failed")


def main():
    """Main entry point."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    cfg_file = None
    # Handle a different client.yaml other than default
    if arg_line and arg_line[0] == "--local":
        cfg_file = arg_line[1:2]
        arg_line = arg_line[2:]
    parsed = build_parser(arg_line)
    if cfg_file:
        cfg = SuiConfig.from_config_file(cfg_file[0])
    else:
        cfg = SuiConfig.default()

    # Run the job
    _join_coins(sync_client.SuiClient(cfg), parsed)


if __name__ == "__main__":
    main()
