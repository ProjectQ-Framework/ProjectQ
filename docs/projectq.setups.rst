setups
======

The setups package contains a collection of setups which can be loaded by the `MainEngine`. Each setup then loads its own set of decomposition rules and default compiler engines. 

Example:
    .. code-block:: python

        import projectq.setups.ibm
        from projectq import MainEngine
        eng = MainEngine(setup=projectq.setups.ibm)
        # eng uses the default Simulator backend

Note:
	One can either provide an `engine_list` or a `setup` to the `MainEngine` but not both.

The subpackage decompositions contains all the individual decomposition rules
which can be given to, e.g., an `AutoReplacer`.


Subpackages
-----------

.. toctree::
    :maxdepth: 1

    projectq.setups.decompositions

Submodules
----------

Each of the submodules contains a setup which can be loaded by the `MainEngine` :

.. autosummary::

    projectq.setups.default
    projectq.setups.ibm
    projectq.setups.ibm16

default
-------

.. automodule:: projectq.setups.default
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

Module contents
---------------

.. automodule:: projectq.setups
    :members:
    :special-members: __init__
