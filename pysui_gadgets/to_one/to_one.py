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


from pysui import SyncClient, SuiConfig, handle_result
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_utils import partition
from pysui_gadgets.utils.cmdlines import to_one_parser
from pysui_gadgets.utils.exec_helpers import add_owner_to_gas_object


def _join_coins(client: SyncClient, args: argparse.Namespace):
    """Using PayAllSui builder, join all mists from all gas object to one for an address."""
    gas_res: list = handle_result(client.get_gas(args.address, True)).data
    if len(gas_res) < 2:
        print("Can't join with less than 2 coins")
        return
    # Resolve primary by argument or selection
    if args.primary:
        index = [x.object_id for x in gas_res].index(args.primary.value)
        primary = gas_res.pop(index)
    else:
        primary = gas_res[0]
        gas_res = gas_res[1:]
    owner = args.address.address
    gas_res = [add_owner_to_gas_object(owner, x) for x in gas_res]
    converted = 0

    if len(gas_res) <= args.merge_threshold:
        txn = SyncTransaction(client, initial_sender=args.address)
        _ = txn.merge_coins(merge_to=txn.gas, merge_from=gas_res)
        result = txn.execute(use_gas_object=primary.object_id)
    else:
        # Partition the gas_res into _MAX_INPUTS chunks
        for chunk in list(partition(gas_res, args.merge_threshold)):
            chunk_count = len(chunk)
            txn = SyncTransaction(client, initial_sender=args.address)
            _ = txn.merge_coins(merge_to=txn.gas, merge_from=chunk)
            result = txn.execute(use_gas_object=primary.object_id)
            if result.is_ok():
                converted += chunk_count
            else:
                print(f"Failure on coin in range {converted} -> {result.result_string}")
                return
    print(f"Succesfully merged {converted} coins to {primary.object_id}")
    print(handle_result(client.get_object(primary.object_id)).to_json(indent=2))


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
    parsed = to_one_parser(arg_line)
    if cfg_file:
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()

    # Run the job
    _join_coins(SyncClient(cfg), parsed)


if __name__ == "__main__":
    main()
