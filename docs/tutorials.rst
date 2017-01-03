.. _tutorial:

Tutorial
========

.. toctree::
   :maxdepth: 2	

Getting started
---------------

To start using ProjectQ, simply run

.. code-block:: bash

	python -m pip install --user projectq

or, alternatively, `clone/download <https://github.com/projectq-framework>`_ this repo (e.g., to your /home directory) and run

.. code-block:: bash

	cd /home/projectq
	python -m pip install --user .

.. note::
	The setup will try to build a C++-Simulator, which is much faster than the Python implementation. If it fails, you may use the `--without-cppsimulator` parameter, i.e., 
	
	.. code-block:: bash
	
		python -m pip install --user --global-option=--without-cppsimulator .
	
	and the framework will use the **slow Python simulator instead**. Note that this only works if the installation has been tried once without the `--without-cppsimulator` parameter and hence all requirements are now installed. See the instructions below if you want to run larger simulations. The Python simulator works perfectly fine for the small examples (e.g., running Shor's algorithm for factoring 15 or 21).

.. note::
	If building the C++-Simulator does not work out of the box, consider specifying a different compiler. For example:
	
	.. code-block:: bash
	
			env CC=g++-5 python -m pip install --user projectq

	Please note that the compiler you specify must support **C++11**!


Detailed instructions and OS-specific hints
-------------------------------------------

**Ubuntu**:
	After having installed the build tools (for g++):

	.. code-block:: bash
	
		sudo apt-get install build-essential
	
	You only need to install Python (and the package manager). For version 3, run
	
	.. code-block:: bash
	
		sudo apt-get install python3 python3-pip
	
	When you then run
	
	.. code-block:: bash
		
		sudo pip3 install --user projectq
	
	all dependencies (such as numpy and pybind11) should be installed automatically.


**Windows**:
	It is easiest to install a pre-compiled version of Python, including numpy and many more useful packages. One way to do so is using, e.g., the Python3.5 installers from `python.org <https://www.python.org/downloads>`_ or `ANACONDA <https://www.continuum.io/downloads>`_. Installing ProjectQ right away will succeed for the (slow) Python simulator (i.e., with the `--without-cppsimulator` flag). For a compiled version of the simulator, install the Visual C++ Build Tools and the Microsoft Windows SDK prior to doing a pip install. The built simulator will not support multi-threading due to the limited OpenMP support of msvc.

	Should you want to run multi-threaded simulations, you can install a compiler which supports newer OpenMP versions, such as MinGW GCC and then manually build the C++ simulator with OpenMP enabled.


**macOS**:
	These are the steps to install ProjectQ on a new Mac:

	Install XCode:

	.. code-block:: bash

		xcode-select --install

	Next, you need to install Python and pip. One way of doing so is using macports to install Python 3.5 and the corresponding version of pip. Visit `macports.org <https://www.macports.org/install.php>`_ and install the latest version (afterwards open a new terminal). Then, use macports to install Python 3.5 by

	.. code-block:: bash

		sudo port install python35

	It might show a warning that if you intend to use python from the terminal, you should also install

	.. code-block:: bash

		sudo port install py35-readline

	Install pip by

	.. code-block:: bash

		sudo port install py35-pip

	Next, we can install ProjectQ with the high performance simulator written in C++. Therefore, we first need to install a suitable compiler which supports OpenMP and instrinsics. One option is to install clang 3.9 also using macports (note: gcc installed via macports does not work as the gcc compiler claims to support instrinsics, while the assembler of gcc does not support it)

	.. code-block:: bash

		sudo port install clang-3.9

	ProjectQ is now installed by:

	.. code-block:: bash

		env CC=clang-mp-3.9 env CXX=clang++-mp-3.9 python3.5 -m pip install --user projectq

	If you don't want to install clang 3.9, you can try and specify your preferred compiler by changing CC and CXX in the above command (the compiler must support **C++11**). 

	Should something go wrong when compiling the C++ simulator extension in one of the above installation procedures, 
	you can turn off this feature using the ``--without-cppsimulator`` 
	parameter (note: this only works if one of the above installation methods has been tried and hence 
	all requirements are now installed), i.e.,

	.. code-block:: bash
	
		python3.5 -m pip install --user --global-option=--without-cppsimulator projectq

	While this simulator works fine for small examples, it is suggested to install the high performance simulator written in C++. 

	If you just want to install ProjectQ with the (slow) Python simulator and no compiler, then first try to install ProjectQ with the default compiler 

	.. code-block:: bash

		python3.5 -m pip install --user projectq

	which most likely will fail and then use the command above using the ``--without-cppsimulator`` 
	parameter.



Basic quantum program
---------------------

To check whether the installation worked, try running the following basic example:

.. code-block:: python

	from projectq import MainEngine  # import the main compiler engine
	from projectq.ops import H, Measure  # import the operations we want to perform (Hadamard and measurement)
	
	eng = MainEngine()  # create a default compiler (the back-end is a simulator)
	qubit = eng.allocate_qubit()  # allocate 1 qubit
	
	H | qubit  # apply a Hadamard gate
	Measure | qubit  # measure the qubit
	
	eng.flush()  # flush all gates (and execute measurements)
	print("Measured {}".format(int(qubit)))  # output measurement result

Which creates random bits (0 or 1).
