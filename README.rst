pysui-gadgets
=============

pysui-gadgets includes tools and utilities that work with the pysui SDK.

Gadgets included:

* package - Performs operations that leverages meta-data about SUI move packages (smart-contracts)

Setup
*****

#. Install SUI binaries (devnet is currently supported)
#. Setup python virtual environment
#. Activate virtual environment
#. Update ``pip``
#. Install ``pysui``

.. code-block::

    cargo install --locked --git https://github.com/MystenLabs/sui.git --branch devnet sui
    python3 -m venv env
    . env/bin/activate
    pip install -U pip
    pip install -r requirements.txt
