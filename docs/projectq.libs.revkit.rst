revkit
======

This library integrates `RevKit <https://msoeken.github.io/revkit.html>`_ into
ProjectQ to allow some automatic synthesis routines for reversible logic.  The
library adds the following operations that can be used to construct quantum
circuits:

- :class:`~projectq.libs.revkit.ControlFunctionOracle`: Synthesizes a reversible circuit from Boolean control function
- :class:`~projectq.libs.revkit.PermutationOracle`: Synthesizes a reversible circuit for a permutation
- :class:`~projectq.libs.revkit.PhaseOracle`: Synthesizes phase circuit from an arbitrary Boolean function

RevKit can be installed from PyPi with `pip install revkit`.

.. note::

    The RevKit Python module must be installed in order to use this ProjectQ library.

    There exist precompiled binaries in PyPi, as well as a source distribution.
    Note that a C++ compiler with C++17 support is required to build the RevKit
    python module from source.  Examples for compatible compilers are Clang
    6.0, GCC 7.3, and GCC 8.1.

The integration of RevKit into ProjectQ and other quantum programming languages is described in the paper

    * Mathias Soeken, Thomas Haener, and Martin Roetteler "Programming Quantum Computers Using Design Automation," in: Design Automation and Test in Europe (2018) [`arXiv:1803.01022 <https://arxiv.org/abs/1803.01022>`_]

Module contents
---------------

.. automodule:: projectq.libs.revkit
    :members:
    :special-members: __init__,__or__
    :imported-members:
