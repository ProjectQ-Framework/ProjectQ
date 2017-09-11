ProjectQ - An open source software framework for quantum computing
==================================================================

.. image:: https://travis-ci.org/ProjectQ-Framework/ProjectQ.svg?branch=master
    :target: https://travis-ci.org/ProjectQ-Framework/ProjectQ

.. image:: https://coveralls.io/repos/github/ProjectQ-Framework/ProjectQ/badge.svg
    :target: https://coveralls.io/github/ProjectQ-Framework/ProjectQ

.. image:: https://readthedocs.org/projects/projectq/badge/?version=latest
    :target: http://projectq.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/projectq.svg
    :target: https://badge.fury.io/py/projectq
    
.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5%2C%203.6-brightgreen.svg


ProjectQ is an open source effort for quantum computing.

It features a compilation framework capable of
targeting various types of hardware, a high-performance quantum computer
simulator with emulation capabilities, and various compiler plug-ins.
This allows users to

-  run quantum programs on the IBM Quantum Experience chip
-  simulate quantum programs on classical computers
-  emulate quantum programs at a higher level of abstraction (e.g.,
   mimicking the action of large oracles instead of compiling them to
   low-level gates)
-  export quantum programs as circuits (using TikZ)
-  get resource estimates

Getting started
---------------

To start using ProjectQ, simply follow the installation instructions in the `tutorials <http://projectq.readthedocs.io/en/latest/tutorials.html>`__. There, you will also find OS-specific hints, a small introduction to the ProjectQ syntax, and a few `code examples <http://projectq.readthedocs.io/en/latest/examples.html>`__. More example codes and tutorials can be found in the examples folder `here <https://github.com/ProjectQ-Framework/ProjectQ/tree/develop/examples>`__ on GitHub.

Also, make sure to check out the `ProjectQ
website <http://www.projectq.ch>`__ and the detailed `code documentation <http://projectq.readthedocs.io/en/latest/>`__.

How to contribute
-----------------

For information on how to contribute, please visit the `ProjectQ
website <http://www.projectq.ch>`__ or send an e-mail to
info@projectq.ch.

Please cite
-----------

When using ProjectQ for research projects, please cite

-  Damian S. Steiger, Thomas Häner, and Matthias Troyer "ProjectQ: An
   Open Source Software Framework for Quantum Computing"
   `[arxiv:1612.08091] <https://arxiv.org/abs/1612.08091>`__
-  Thomas Häner, Damian S. Steiger, Krysta M. Svore, and Matthias Troyer
   "A Software Methodology for Compiling Quantum Programs"
   `[arxiv:1604.01401] <http://arxiv.org/abs/1604.01401>`__

Authors
-------

The first release of ProjectQ (v0.1) was developed by `Thomas
Häner <http://www.comp.phys.ethz.ch/people/person-detail.html?persid=179208>`__
and `Damian S.
Steiger <http://www.comp.phys.ethz.ch/people/person-detail.html?persid=165677>`__
in the group of `Prof. Dr. Matthias
Troyer <http://www.comp.phys.ethz.ch/people/troyer.html>`__ at ETH
Zurich.

License
-------

ProjectQ is released under the Apache 2 license.
