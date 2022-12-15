pysui-gadgets
=============

pysui-gadgets includes tools and utilities that work with the pysui SDK.

Gadgets included:

* package - Performs operations that leverages meta-data about SUI move packages (smart-contracts)
* dsl-gen - Creates python representation of move package key structs and entry point functions

Setup for use
*************

#. Install SUI binaries (devnet is currently supported)
#. Setup python virtual environment
#. Activate virtual environment
#. Update ``pip``
#. Install ``pysui_gadgets``

.. code-block::

    cargo install --locked --git https://github.com/MystenLabs/sui.git --branch devnet sui
    python3 -m venv env
    . env/bin/activate
    pip install -U pip
    pip install pysui_gadgets

Setup for cloning
*****************

#. Install SUI binaries (devnet is currently supported)
#. Clone ``pysui_gadgets`` repository
#. Setup python virtual environment
#. Activate virtual environment
#. Update ``pip``
#. Install ``pysui``

.. code-block::

    cargo install --locked --git https://github.com/MystenLabs/sui.git --branch devnet sui
    git clone git@github.com:FrankC01/pysui_gadgets.git
    python3 -m venv env
    . env/bin/activate
    pip install -U pip
    pip install pysui


Running gadgets
***************

.. code-block::

    package -h
    dsl-gen -h
