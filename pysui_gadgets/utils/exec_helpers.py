#    Copyright  Frank V. Castellucci
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

"""pysui-gadget: transaction execution helpers.

Provides low level transaction execution prep or submit options.
"""
import base64
from typing import Optional
from pysui import SuiAddress, SuiConfig
from pysui.sui.sui_txresults.single_tx import AddressOwner, SuiCoinObject
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn


def add_owner_to_gas_object(owner: str, gas_coin: SuiCoinObject) -> SuiCoinObject:
    """Imbue coin to optimize argument resolution."""
    setattr(
        gas_coin,
        "owner",
        AddressOwner(owner_type="AddressOwner", address_owner=owner),
    )
    return gas_coin


def util_resolve_owner(
    config: SuiConfig, owner: Optional[SuiAddress], alias: Optional[str]
):
    """util_resolve_owner Resolve ownership between implicit or alias values.

    This will set the configurations active address if it isn't already

    :param config: Active pysui Sui Configuration
    :type config: SuiConfig
    :param owner: An explicit owner, optional
    :type owner: Optional[SuiAddress]
    :param alias: An alias of owner, optional
    :type alias: Optional[str]
    :raises ValueError: If both owner and alias are None
    :raises ValueError: If resulting owner is not a member of the configuration
    """
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


def util_get_all_owner_gas(
    client: SuiGQLClient, owner: str
) -> list[pgql_type.SuiCoinObjectGQL]:
    """util_get_all_owner_gas Fetches all gas objects for owner.

    :param client: The active Sui GraphQL client
    :type client: SuiGQLClient
    :param owner: The owners address string (e.g. "0x...")
    :type owner: str
    :raises ValueError: If the query returns an error
    :raises ValueError: If there is no gas known for owner
    :return: List of gas coins for owner
    :rtype: list[pgql_type.SuiCoinObjectGQL]
    """
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
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
        raise ValueError(f"{owner} has no Sui gas coins")
    return coin_list


def util_inspect(
    client: SuiGQLClient, txn: SuiTransaction, target_gas=pgql_type.SuiCoinObjectGQL
):
    """."""
    tx_kind = txn.raw_kind()
    print(tx_kind.to_json(indent=2))
    tx_b64 = base64.b64encode(tx_kind.serialize()).decode()
    options = {
        "sender": client.config.active_address.address,
        # "gasObjects": [
        #     {
        #         "address": target_gas.object_id,
        #         "digest": target_gas.object_digest,
        #         "version": target_gas.version,
        #     }
        # ],
    }
    drtk = qn.DryRunTransactionKind(tx_bytestr=tx_b64, tx_meta=options)
    result = client.execute_query_node(with_node=drtk)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        raise ValueError(f"Error in dry run {result.result_string}")


def util_execute(
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
        raise ValueError(f"Error in execution {result.result_string}")
