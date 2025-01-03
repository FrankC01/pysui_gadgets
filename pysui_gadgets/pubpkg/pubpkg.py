#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pubpkg - Determine packages install based on upgrade key."""


import sys

from pysui import PysuiConfiguration, SyncGqlClient, SuiRpcResult
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type


def main():
    """Main entry point."""
    # Parse module meta data pulling out relevant content
    # to generate struct->class and functions->class
    arg_line = sys.argv[1:].copy()
    cfg: PysuiConfiguration = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP  # , profile_name="testnet"
    )
    client: SyncGqlClient = SyncGqlClient(pysui_config=cfg)
    result: SuiRpcResult = client.execute_query_node(
        with_node=qn.GetObjectsOwnedByAddress(owner=cfg.active_address)
    )
    if result.is_ok():
        objs: pgql_type.ObjectReadsGQL = result.result_data
        for _, obj in enumerate(objs.data):
            if obj.object_type.endswith("package::UpgradeCap"):
                print(obj.object_id)
    print()


if __name__ == "__main__":
    try:
        main()
    except TypeError as tye:
        print(tye.args)
