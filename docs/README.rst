Documentation
=============

You want to learn more about Socon. You are at the right place!
This section will help you generate the documentation to read it on your
favorite browser. No worries, if you don't want to do that, every files in this
tree are plain text and can be viewed using any text file reader.

All the documentation uses `ReST`_ (reStructuredText), and the famous
`Sphinx`_ documentation system.

To generate the docs, please follow the steps below:

* Install Sphinx (using ``python -m pip install Sphinx``).

* In this docs/ directory, type ``make html`` (or ``make.bat html`` on
  Windows) at a shell prompt.

When the documentation is fully generated, you can find the "index.html" page
here: ``_build/html/index.html``

.. _ReST: https://docutils.sourceforge.io/rst.html
.. _Sphinx: https://www.sphinx-doc.org/
