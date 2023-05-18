pysui-gadgets
=============

pysui-gadgets includes tools and utilities that work with the pysui SDK.

Gadgets included:

* package - Performs operations that leverages meta-data about SUI move packages (smart-contracts)
* dsl-gen - Creates python representation of move package key structs and entry point functions
* to-one - Merges all SUI Gas mists 'to one' SUI Gas object for an address

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
    pip install --use-pep517 pysui_gadgets

Setup for cloning
*****************

#. Install SUI binaries (devnet is currently supported)
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

    module -h
    package -h
    dslgen -h
    to-one -h
    splay -h
