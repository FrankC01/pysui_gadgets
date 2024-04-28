pysui-gadgets
=============

pysui-gadgets includes tools and utilities that work with the pysui SDK.

Gadgets included:

* package - Performs operations that leverages meta-data about SUI move packages (smart-contracts)
* dsl-gen - Creates python representation of move package key structs and entry point functions
* to-one - Merges all SUI Gas mists 'to one' SUI Gas object for an address
* splay - Evenly distribute coins from one address to many
* vh - History of object versions

Setup for use
*************

#. Install SUI binaries
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

Upgrade
*******

#. Activate virtual environment
#. Update ``pysui_gadgets``

.. code-block::

    . env/bin/activate
    pip install -U pysui_gadgets

Setup for cloning
*****************

#. Install SUI binaries
#. Clone ``pysui_gadgets`` repository
#. Setup python virtual environment
#. Activate virtual environment
#. Update ``pip``
#. Install ``pysui``
#. Alternate install of ``pysui``

.. code-block::

    cargo install --locked --git https://github.com/MystenLabs/sui.git --branch devnet sui
    git clone git@github.com:FrankC01/pysui_gadgets.git
    python3 -m venv env
    . env/bin/activate
    pip install -U pip
    pip install -r requirements.txt
    # Alternately
    # clone pysui to other folder
    # in pysui run bin/package-build.sh
    # back in here
    pip install ../path_to_pysui/


Running gadgets
***************

.. code-block::

    splay -h
    to-one -h
    vh -h
    module -h
    package -h
    dslgen -h

splay
~~~~~

Evenly distribute gas objects across one or more addresses. Can also splay to owner itself.
