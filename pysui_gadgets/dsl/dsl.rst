
pysui gadget: DSL
=================

The pysui DSL gadget generates python classes from meta-data of a SUI move module.

This enables python sui client developers to operate in a context of the move package they
interact with.

Notes about DSL generation from normalized sui packages

#. Only concerned about structs with Key ability. Those structs without key ability are ignored.
#. Only concerned with entry point functions. Public and private module functions are ignored.
#. Generics are ignored

For example, running `dsl -p 0x2 -i coin -o somefolder/path` will create/overwrite:

.. code-block:: bash

    _0x2 <--- package id
        coin <--- Module folder
            ``__init__.py``
            ``models.py``   <--- Contains the structs in coin that,at least, has key ability (i.e. struct has Key)
            ``coin.py``     <--- Contains Coin class with ``def funcs`` where funcs are modules ``public entry fun...``
