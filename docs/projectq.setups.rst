setups
======

The setups package contains a collection of setups which can be loaded by the `MainEngine`. Each setup contains a `get_engine_list` function which returns a list of compiler engines:

Example:
    .. code-block:: python

        import projectq.setups.ibm as ibm_setup
        from projectq import MainEngine
        eng = MainEngine(engine_list=ibm_setup.get_engine_list())
        # eng uses the default Simulator backend

The subpackage decompositions contains all the individual decomposition rules
which can be given to, e.g., an `AutoReplacer`.


Subpackages
-----------

.. toctree::
    :maxdepth: 1

    projectq.setups.decompositions

Submodules
----------

Each of the submodules contains a setup which can be used to specify the
`engine_list` used by the `MainEngine` :

.. autosummary::

    projectq.setups.default
    projectq.setups.grid
    projectq.setups.ibm
    projectq.setups.ibm16
    projectq.setups.linear
    projectq.setups.restrictedgateset

default
-------

.. automodule:: projectq.setups.default
    :members:
    :special-members: __init__
    :undoc-members:

grid
----

.. automodule:: projectq.setups.grid
    :members:
    :special-members: __init__
    :undoc-members:

ibm
---

.. automodule:: projectq.setups.ibm
    :members:
    :special-members: __init__
    :undoc-members:

ibm16
-----

.. automodule:: projectq.setups.ibm16
    :members:
    :special-members: __init__
    :undoc-members:

linear
------

.. automodule:: projectq.setups.linear
    :members:
    :special-members: __init__
    :undoc-members:

restrictedgateset
-----------------

.. automodule:: projectq.setups.restrictedgateset
    :members:
    :special-members: __init__
    :undoc-members:

Module contents
---------------

.. automodule:: projectq.setups
    :members:
    :special-members: __init__
