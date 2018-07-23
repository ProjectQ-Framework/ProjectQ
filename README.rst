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
    
.. image:: https://img.shields.io/badge/python-2.7%2C%203.4%2C%203.5%2C%203.6-brightgreen.svg


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

Examples
--------

**First quantum program**

.. code-block:: python

    from projectq import MainEngine  # import the main compiler engine
    from projectq.ops import H, Measure  # import the operations we want to perform (Hadamard and measurement)

    eng = MainEngine()  # create a default compiler (the back-end is a simulator)
    qubit = eng.allocate_qubit()  # allocate a quantum register with 1 qubit

    H | qubit  # apply a Hadamard gate
    Measure | qubit  # measure the qubit

    eng.flush()  # flush all gates (and execute measurements)
    print("Measured {}".format(int(qubit)))  # converting a qubit to int or bool gives access to the measurement result


ProjectQ features a lean syntax which is close to the mathematical notation used in quantum physics. For example, a rotation of a qubit around the x-axis is usually specified as:

.. image:: docs/images/braket_notation.svg
    :alt: Rx(theta)|qubit>
    :width: 100px

The same statement in ProjectQ's syntax is:

.. code-block:: python

    Rx(theta) | qubit

The **|**-operator separates the specification of the gate operation (left-hand side) from the quantum bits to which the operation is applied (right-hand side).

**Changing the compiler and using a resource counter as a back-end**

Instead of simulating a quantum program, one can use our resource counter (as a back-end) to determine how many operations it would take on a future quantum computer with a given architecture. Suppose the qubits are arranged on a linear chain and the architecture supports any single-qubit gate as well as the two-qubit CNOT and Swap operations:

.. code-block:: python

    from projectq import MainEngine
    from projectq.backends import ResourceCounter
    from projectq.ops import QFT
    from projectq.setups import linear

    compiler_engines = linear.get_engine_list(num_qubits=16,
                                              one_qubit_gates='any',
                                              two_qubit_gates=(CNOT, Swap))
    resource_counter = ResourceCounter()
    eng = MainEngine(backend=resource_counter, engine_list=compiler_engines)
    qureg = eng.allocate_qureg(16)
    QFT | qureg
    eng.flush()

    print(resource_counter)

    # This will output, among other information,
    # how many operations are needed to perform
    # this quantum fourier transform (QFT), i.e.,
    #   Gate class counts:
    #       AllocateQubitGate : 16
    #       CXGate : 240
    #       HGate : 16
    #       R : 120
    #       Rz : 240
    #       SwapGate : 262


**Running a quantum program on IBM's QE chips**

To run a program on the IBM Quantum Experience chips, all one has to do is choose the `IBMBackend` and the corresponding compiler:

.. code-block:: python

    compiler_engines = projectq.setups.ibm16.get_engine_list()
    eng = MainEngine(IBMBackend(use_hardware=True, num_runs=1024,
                                verbose=False, device='ibmqx5'),
                     engine_list=compiler_engines)


**Classically simulate a quantum program**

ProjectQ has a high-performance simulator which allows simulating up to about 30 qubits on a regular laptop. See the `simulator tutorial <https://github.com/ProjectQ-Framework/ProjectQ/blob/feature/update-readme/examples/simulator_tutorial.ipynb>`__ for more information. Using the emulation features of our simulator (fast classical shortcuts), one can easily emulate Shor's algorithm for problem sizes for which a quantum computer would require above 50 qubits, see our `example codes <http://projectq.readthedocs.io/en/latest/examples.html#shor-s-algorithm-for-factoring>`__.


The advanced features of the simulator are also particularly useful to investigate algorithms for the simulation of quantum systems. For example, the simulator can evolve a quantum system in time (without Trotter errors) and it gives direct access to expectation values of Hamiltonians leading to extremely fast simulations of VQE type algorithms:

.. code-block:: python
    
    from projectq import MainEngine
    from projectq.ops import All, Measure, QubitOperator, TimeEvolution

    eng = MainEngine()
    wavefunction = eng.allocate_qureg(2)
    # Specify a Hamiltonian in terms of Pauli operators:
    hamiltonian = QubitOperator("X0 X1") + 0.5 * QubitOperator("Y0 Y1")
    # Apply exp(-i * Hamiltonian * time) (without Trotter error)
    TimeEvolution(time=1, hamiltonian=hamiltonian) | wavefunction
    # Measure the expection value using the simulator shortcut:
    eng.flush()
    value = eng.backend.get_expectation_value(hamiltonian, wavefunction)

    # Last operation in any program should be measuring all qubits
    All(Measure) | qureg
    eng.flush()



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
   `Quantum 2, 49 (2018) <https://doi.org/10.22331/q-2018-01-31-49>`__
   (published on `arXiv <https://arxiv.org/abs/1612.08091>`__ on 23 Dec 2016)
-  Thomas Häner, Damian S. Steiger, Krysta M. Svore, and Matthias Troyer
   "A Software Methodology for Compiling Quantum Programs" `Quantum Sci. Technol. 3 (2018) 020501 <https://doi.org/10.1088/2058-9565/aaa5cc>`__ 
   (published on `arXiv <http://arxiv.org/abs/1604.01401>`__ on 5 Apr 2016)

Authors
-------

The first release of ProjectQ (v0.1) was developed by `Thomas
Häner <http://www.comp.phys.ethz.ch/people/person-detail.html?persid=179208>`__
and `Damian S.
Steiger <http://www.comp.phys.ethz.ch/people/person-detail.html?persid=165677>`__
in the group of `Prof. Dr. Matthias
Troyer <http://www.comp.phys.ethz.ch/people/troyer.html>`__ at ETH
Zurich.

ProjectQ is constantly growing and `many other people <https://github.com/ProjectQ-Framework/ProjectQ/graphs/contributors>`__ have already contributed to it in the meantime.

License
-------

ProjectQ is released under the Apache 2 license.
