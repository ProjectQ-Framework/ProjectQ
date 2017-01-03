ProjectQ - An open source software framework for quantum computing
==================================================================

.. image:: https://travis-ci.org/ProjectQ-Framework/ProjectQ.svg?branch=master
    :target: https://travis-ci.org/ProjectQ-Framework/ProjectQ

.. image:: https://coveralls.io/repos/github/ProjectQ-Framework/ProjectQ/badge.svg
    :target: https://coveralls.io/github/ProjectQ-Framework/ProjectQ


ProjectQ is an open source effort for quantum computing.

The first version (v0.1) features a compilation framework capable of
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

To start using ProjectQ, simply run

.. code:: bash

    python -m pip install --user projectq

Details regarding the installation on different operating systems can be
found in the documentation (`getting started <http://projectq.ch/docs/tutorials.html#getting-startedd>`__).
Alternatively, you can clone or download this repository and run

.. code:: bash

    python setup.py install --user

or

.. code:: bash

    python -m pip install --user .

Should something go wrong when compiling the C++ simulator extension in one of the above installation procedures,
you can turn off this feature using the ``--without-cppsimulator``
parameter (note: this only works if one of the above installation methods has been tried and hence 
all requirements are now installed), i.e.,

.. code:: bash

    python setup.py --without-cppsimulator install --user

If you are using pip, then this parameter can be supplied as follows

.. code:: bash

    python -m pip install --global-option=--without-cppsimulator --user .

Then, please visit the `ProjectQ website <http://www.projectq.ch>`__,
where you will find
`tutorials <http://projectq.ch/docs/tutorials.html>`__,
`code examples <http://projectq.ch/docs/examples.html>`__, and the
`documentation <http://projectq.ch/docs/>`__.

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
