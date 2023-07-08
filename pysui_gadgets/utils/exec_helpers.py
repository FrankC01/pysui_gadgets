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

from pysui.sui.sui_txresults.single_tx import AddressOwner, SuiCoinObject


def add_owner_to_gas_object(owner: str, gas_coin: SuiCoinObject) -> SuiCoinObject:
    """Imbue coin to optimize argument resolution."""
    setattr(
        gas_coin,
        "owner",
        AddressOwner(owner_type="AddressOwner", address_owner=owner),
    )
    return gas_coin
