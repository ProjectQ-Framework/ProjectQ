Examples and Tutorials
======================

This folder contains a collection of **examples** and **tutorials** for how to use ProjectQ. They offer a great way to get started. While this collection is growing, it will never be possible to cover everything. Therefore, we refer the readers to also have a look at:

* Our complete **code documentation** which can be found online `here <http://projectq.readthedocs.io/en/latest/>`__. Besides the newest version of the documentation it also provides older versions. Moreover, these docs can be downloaded for offline usage.

* Our **unit tests**. More than 99% of all lines of code are covered with various unit tests since the first release. Tests are really important to us. Therefore, if you are wondering how a specific feature can be used, have a look at the **unit tests**, where you can find plenty of examples. Finding the unit tests is very easy: E.g., the tests of the simulator implemented in *ProjectQ/projectq/backends/_sim/_simulator.py* can all be found in the same folder in the file *ProjectQ/projectq/backends/_sim/_simulator_test.py*.

Getting started / background information
----------------------------------------

It might be a good starting point to have a look at our paper which explains the goals of the ProjectQ framework and also gives a good overview:

* Damian S. Steiger, Thomas Häner, and Matthias Troyer "ProjectQ: An Open Source Software Framework for Quantum Computing" `[arxiv:1612.08091] <https://arxiv.org/abs/1612.08091>`__

Examples and tutorials in this folder
-------------------------------------

1. Some of the files in this folder are explained in the `documentation <http://projectq.readthedocs.io/en/latest/examples.html>`__.

2. Take a look at the *simulator_tutorial.ipynb* for a detailed introduction to most of the features of our high performance quantum simulator.

3. Running on the IBM QE chip is explained in more details in *ibm_entangle.ipynb*.

4. A small tutorial on the compiler is available in *compiler_tutorial.ipynb* which explains how to compile to a specific gate set.
