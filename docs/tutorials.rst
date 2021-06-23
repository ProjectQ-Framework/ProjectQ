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

Since version 0.6.0, ProjectQ is available as pre-compiled binary wheels in addition to the traditional source package. These wheels should work on most platforms, provided that your processor supports AVX2 instructions. Should you encounter any troubles while installation ProjectQ in binary form, you can always try tom compile the project manually as described below. You may want to pass the `--no-binary projectq` flag to Pip during the installation to make sure that you are downloading the source package.

Alternatively, you can also `clone/download <https://github.com/projectq-framework>`_ this repository (e.g., to your /home directory) and run

.. code-block:: bash

    cd /home/projectq
    python -m pip install --user .

ProjectQ comes with a high-performance quantum simulator written in C++. Please see the detailed OS specific installation instructions below to make sure that you are installing the fastest version.

.. note::
    The setup will try to build a C++-Simulator, which is much faster than the Python implementation. If the C++ compilation were to fail, the setup will install a pure Python implementation of the simulator instead. The Python simulator should work fine for small examples (e.g., running Shor's algorithm for factoring 15 or 21).

    If you want to skip the installation of the C++-Simulator altogether, you can define the ``DISABLE_PROJECTQ_CEXT`` environment variable to avoid any compilation steps.

.. note::
    If building the C++-Simulator does not work out of the box, consider specifying a different compiler. For example:

    .. code-block:: bash

            env CC=g++-10 python -m pip install --user projectq

    Please note that the compiler you specify must support at least **C++11**!

.. note::
    Please use pip version v6.1.0 or higher as this ensures that dependencies are installed in the `correct order <https://pip.pypa.io/en/stable/reference/pip_install/#installation-order>`_.

.. note::
    ProjectQ should be installed on each computer individually as the C++ simulator compilation creates binaries which are optimized for the specific hardware on which it is being installed (potentially using our AVX version and `-march=native`). Therefore, sharing the same ProjectQ installation across different hardware may cause some problems.

**Install AWS Braket Backend requirement**

AWS Braket Backend requires the use of the official AWS SDK for Python, Boto3. This is an extra requirement only needed if you plan to use the AWS Braket Backend. To install ProjectQ inluding this requirement you can include it in the installation instruction as

.. code-block:: bash

    python -m pip install --user projectq[braket]


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

        sudo python3 -m pip install --user projectq

    all dependencies (such as numpy and pybind11) should be installed automatically.


**ArchLinux/Manjaro**:

        Make sure that you have a C/C++ compiler installed:

    .. code-block:: bash

        sudo pacman -Syu gcc

    You only need to install Python (and the package manager). For version 3, run

    .. code-block:: bash

        sudo pacman -Syu python python-pip

    When you then run

    .. code-block:: bash

        sudo python3 -m pip install --user projectq

    all dependencies (such as numpy and pybind11) should be installed automatically.


**Windows**:

    It is easiest to install a pre-compiled version of Python, including numpy and many more useful packages. One way to do so is using, e.g., the Python 3.7 installers from `python.org <https://www.python.org/downloads>`_ or `ANACONDA <https://www.continuum.io/downloads>`_. Installing ProjectQ right away will succeed for the (slow) Python simulator. For a compiled version of the simulator, install the Visual C++ Build Tools and the Microsoft Windows SDK prior to doing a pip install. The built simulator will not support multi-threading due to the limited OpenMP support of the Visual Studio compiler.

    If the Python executable is added to your PATH (option normally suggested at the end of the Python installation procedure), you can then open a cmdline window (WIN + R, type "cmd" and click *OK*) and enter the following in order to install ProjectQ:

    .. code-block:: batch

        python -m pip install --user projectq


    Should you want to run multi-threaded simulations, you can install a compiler which supports newer OpenMP versions, such as MinGW GCC and then manually build the C++ simulator with OpenMP enabled.


**macOS**:

        Similarly to the other platforms, installing ProjectQ without the C++ simulator is really easy:

    .. code-block:: bash

        python3 -m pip install --user projectq


    In order to install the fast C++ simulator, we require that a C++ compiler is installed on your system. There are essentially three options you can choose from:

    1. Using the compiler provided by Apple through the XCode command line tools.
    2. Using Homebrew
    3. Using MacPorts

    For both options 2 and 3, you will be required to first install the XCode command line tools


    **Apple XCode command line tool**

    Install the XCode command line tools by opening a terminal window and running the following command:

    .. code-block:: bash

        xcode-select --install

    Next, you will need to install Python and pip. See options 2 and 3 for information on how to install a newer python version with either Homebrew or MacPorts. Here, we are using the standard python which is preinstalled with macOS. Pip can be installed by:

    .. code-block:: bash

        sudo easy_install pip

    Now, you can install ProjectQ with the C++ simulator using the standard command:

    .. code-block:: bash

        python3 -m pip install --user projectq

    Note that the compiler provided by Apple is currently not able to compile ProjectQ's multi-threaded code.

        **Homebrew**

    First install the XCode command line tools. Then install Homebrew with the following command:

    .. code-block:: bash

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

    Then proceed to install Python as well as a C/C++ compiler (note: gcc installed via Homebrew may lead to some issues):

    .. code-block:: bash

        brew install python llvm

    You should now be able to install ProjectQ with the C++ simulator using the following command:

    .. code-block:: bash

        env P=/usr/local/opt/llvm/bin CC=$P/clang CXX=$P/clang++ python3 -m pip install --user projectq


    **MacPorts**

    Visit `macports.org <https://www.macports.org/install.php>`_ and install the latest version that corresponds to your operating system's version. Afterwards, open a new terminal window.

    Then, use macports to install Python 3.7 by entering the following command

    .. code-block:: bash

        sudo port install python37

    It might show a warning that if you intend to use python from the terminal. In this case, you should also install

    .. code-block:: bash

        sudo port install py37-gnureadline

    Install pip by

    .. code-block:: bash

        sudo port install py37-pip

    Next, we can install ProjectQ with the high performance simulator written in C++. First, we will need to install a suitable compiler with support for **C++11**, OpenMP, and instrinsics. The best option is to install clang 9.0 also using macports (note: gcc installed via macports does not work).

    .. code-block:: bash

        sudo port install clang-9.0

    ProjectQ is now installed by:

    .. code-block:: bash

        env CC=clang-mp-9.0 env CXX=clang++-mp-9.0 /opt/local/bin/python3.7 -m pip install --user projectq


The ProjectQ syntax
-------------------

Our goal is to have an intuitive syntax in order to enable an easy learning curve. Therefore, ProjectQ features a lean syntax which is close to the mathematical notation used in physics.

For example, consider applying an x-rotation by an angle `theta` to a qubit. In ProjectQ, this looks as follows:

.. code-block:: python

    Rx(theta) | qubit

whereas the corresponding notation in physics would be

:math:`R_x(\theta) \; |\text{qubit}\rangle`

Moreover, the `|`-operator separates the classical arguments (on the left) from the quantum arguments (on the right). Next, you will see a basic quantum program using this syntax. Further examples can be found in the docs (`Examples` in the panel on the left) and in the ProjectQ examples folder on `GitHub <https://github.com/ProjectQ-Framework/ProjectQ>`_.

Basic quantum program
---------------------

To check out the ProjectQ syntax in action and to see whether the installation worked, try to run the following basic example

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
