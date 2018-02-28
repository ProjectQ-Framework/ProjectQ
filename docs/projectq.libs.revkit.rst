revkit
======

This library integrates `RevKit <https://msoeken.github.io/revkit.html>`_ into
ProjectQ to allow some automatic synthesis routines for reversible logic.  The
library adds the following operations that can be used to construct quantum
circuits:

- :class:`~projectq.libs.revkit.ControlFunctionOracle`: Synthesizes a reversible circuit from Boolean control function
- :class:`~projectq.libs.revkit.PermutationOracle`: Synthesizes a reversible circuit for a permutation
- :class:`~projectq.libs.revkit.PhaseOracle`: Synthesizes phase circuit from an arbitrary Boolean function

Refer to `RevKit documentation <http://cirkit.readthedocs.io/en/latest/installation.html#python-interface>`_
on how to compile RevKit as a Python module.

.. note::

    The RevKit Python module must be installed in order to use this ProjectQ library.

    There exist precompiled binaries for Ubuntu 14.04 (trusty), 16.04 (xenial), and 17.10 (artful).
    You can install them with::

        sudo add-apt-repository ppa:msoeken/ppa
        sudo apt-get update
        sudo apt-get install cirkit

    These must be run with the Python installation from the distribution (either Python 2.x or Python 3.x).

    For all other systems, RevKit must be compiled from scratch and the RevKit module must be in the Python module path.
    One way to add it is by modifying the ``PYTHONPATH`` environment variable.

The integration of RevKit into ProjectQ and other quantum programming languages is described in the paper

    * Mathias Soeken, Thomas Haener, and Martin Roetteler "Programming Quantum Computers Using Design Automation," in: Design Automation and Test in Europe (2018)

Module contents
---------------

.. automodule:: projectq.libs.revkit
    :members:
    :special-members: __init__,__or__
    :imported-members:
