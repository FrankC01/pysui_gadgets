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

"""pysui-gadget DSL Template.

Copyright Frank V. Castellucci

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from pysui.sui.sui_types import ObjectRead, ObjectID


class _Inner:
    """Base abstraction."""

    def __init__(self, object_id: str):
        """Initialize."""
        self.object_id = object_id

    @property
    def identifier(self) -> ObjectID:
        """Return as ObjectID."""
        return ObjectID(self.object_id)


class _Stub(_Inner):
    """Generated from pysui-dsl."""

    _INIT_FROM_CLASS: bool = False

    def __init__(self, *, object_id: str):
        """Initialize."""
        if not self._INIT_FROM_CLASS:
            raise RuntimeError("Init can only be called from get_instance classmethod.")
        super().__init__(object_id)

    @classmethod
    def get_instance(cls, from_details: ObjectRead):
        """Class thing."""
        cls._INIT_FROM_CLASS = True
        instance = cls(**from_details.data.fields)
        cls._INIT_FROM_CLASS = False
        return instance
