Documentation  
=============

.. image:: https://readthedocs.org/projects/projectq/badge/?version=latest
    :target: http://projectq.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Our detailed code documentation can be found online at `Read the Docs <http://projectq.readthedocs.io/en/latest/>`__ and gets updated automatically. Besides the latest code documentation, there are also previous and offline versions available for download.

Building the docs locally
-------------------------

Before submitting new code, please make sure that the new or changed docstrings render nicely by building the docs manually. To this end, one has to install sphinx and the Read the Docs theme:

.. code-block:: bash

    python -m pip install sphinx
    python -m pip install sphinx_rtd_theme

To build the documentation, navigate to this folder and execute:

.. code-block:: bash

    make clean html

Open _build/html/index.html to view the docs.
