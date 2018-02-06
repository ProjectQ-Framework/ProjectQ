revkit
======

This library integrates `RevKit <https://msoeken.github.io/revkit.html>`_ into
ProjectQ to allow some automatic synthesis routines for reversible logic.  The
library adds the following operations that can be used to construct quantum
circuits:

- :class:`~projectq.libs.revkit.PermutationOracle`: Synthesizes a reversible circuit for a permutation
- :class:`~projectq.libs.revkit.ControlFunctionOracle`: Synthesizes a reversible circuit from Boolean control function

Refer to `RevKit documentation <http://cirkit.readthedocs.io/en/latest/installation.html#python-interface>`_
on how to compile RevKit as a Python module.

.. note::

    The RevKit Python module must be in the Python module path.  You can add
    it by modifying the ``PYTHONPATH`` environment variable.

Module contents
---------------

.. automodule:: projectq.libs.revkit
    :members:
    :special-members: __init__,__or__
    :imported-members:
