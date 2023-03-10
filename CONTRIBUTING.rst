=====================
Contributing to Socon
=====================

We would highly appreciate any kind of contribution to the project. As the
project is still as its premise we need more people than ever. You can
contribute to Socon in many ways by fixing bugs, writing docs, proposing
new features and many more. Every little bit helps!

.. contents::
   :depth: 2
   :backlinks: none

Writing code
============

Whether you're fixing bugs or writing new features, you will need to write
codes. Socon follow specific coding rules that you can retrieve in
the :doc:`coding-style` documentation.

Features
========

New features
------------

We would really like to hear your suggestions.
Feel free to `submit them as issues <https://github.com/socon-dev/socon/issues>`_ and:

* Explain in detail your suggestions and how it works
* If anything in the project is impacted, explain how and why?
* Keep it simple!

Implement features
------------------

Look through the `Github issues for enhancements <https://github.com/socon-dev/socon/issues>`_.
Send an email to `socon-dev@proton.me` or use the
`Socon GitHub discussion <https://github.com/socon-dev/socon/discussions>`_ to find
out how you can implement this feature. To indicate that you are going to work on
that particular feature, please add a comment to that effect on the specific
enhancement.

Bugs
====

Report bugs
-----------

If you are not sure to have see a bug, ask in the
`Socon GitHub discussion <https://github.com/socon-dev/socon/discussions>`_.

You can report bugs for Socon in the
`issue tracker <https://github.com/socon-dev/socon/issues>`. Be sure to integrate
the following when you do so:

* A detailed description of the bug or problem you are having. Well-written
   bug reports are incredibly helpful.
* The operating system you are using and the version.
* Minimum example on how to reproduce the issue.
* The version of Socon you are using.

Fix bugs
--------

Look through the `GiHub issues for bugs <https://github.com/socon-dev/socon/issues>`_.
The same way you would implement a features, send an email to `socon-dev@proton.me`
or use the `Socon GitHub discussion <https://github.com/socon-dev/socon/discussions>`_
to find out how you can implement this feature. To indicate that you are
going to work on that particular bug, please add a comment to that effect on
the specific issue.

Write documentation
===================

Socon can always use more documentation. In some case the documentation might be
unclear or incomplete. We need your to help fix that and make it better. If you have
a writer's soul here is how you can help and what needs to get done:

* Add complementary documentation. Is something unclear? Does it need
   more information?

* Function, class, attributes docstrings. It is really important that the
   end-user get immediately what a function does without reading the documentation.
   Socon use the `Sphinx docstring format <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_.

* Example, topics, how-to documentations are very appreciated.

.. important::

   Socon does not use code docstring to populate the API's documentation. We
   think that too much information in a function description can make it unclear.
   We want docstring to be simple and straight-forward.

The documentation use `Sphinx <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/>`_
documentation system. The basic idea is that lightly-formatted plain-text
documentation is transformed into HTML, PDF, and any other output format.

To build the documentation locally you will have to install Sphinx:

.. code-block:: console

   $ python -m pip -r docs/requirements.txt

Then from the ``docs`` directory, build the html:

.. code-block:: console

   $ make html

The built documentation should be available in ``docs/_build/html``.

How the documentation is organized
----------------------------------

The documentation is organized into several categories:

* :doc:`Tutorials </intro/tutorials/index>` take the reader by the hand through a
   series of basic to complex examples in order to create something. The important
   thing about a tutorials is to help the reader create something useful
   that will help him in the daily use of Socon.

* :doc:`Reference guides </ref/index>` contain technical reference for API's.
   They describe how Socon's internal machinery functions. The important thing
   in the reference guides is to assume that the user already understands the
   basic concepts involved but needs a reminder on how Socon does it.

* :doc:`How-to guides </how-to/index>` take the reader through steps in key
   subjects. The important aspect in that section is that each subject must be
   result-oriented rather than focused on internal details.

Spelling check
--------------

sphinxcontrib.spelling is a spelling checker for Sphinx.
It uses PyEnchant to produce a report showing misspelled words. It is
a good idea to run the tool before you commit your docs.

Then from the ``docs`` directory:

.. code-block:: console

   $ make spelling

Wrong words (if any) along with the file and line number where they occur
will be saved to _build/spelling/output.txt.

.. note::

   If you are sure that you are using a correct word -- add it to
   ``docs/spelling_wordlist``.

Contribute
==========

Contribution is done through pull request from your own Socon repository (fork).
As a quick reminder, a pull request informs Socon's core development team about
the changes that you have submitted. It will allow us to review the code and to make
comment to discuss its potential modification or not.

Find below an example on how to fork Socon and make a pull request:

#. Fork the `Socon <https://github.com/socon-dev/socon>`_. If you don't know how to do
   it, check the `GitHub documentation <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`__
   documentation.

#. Open Git bash, and create your fork locally using git::

   $ git clone git@github.com:YOUR_GITHUB_USERNAME/socon.git
   $ cd socon

#. Create a branch from the ``master`` branch::

   $ git checkout -b your-branch master

#. Add main Socon remote as ``upstream``. This will help you synchronize
   your fork with the main repository.

   $ git remote add upstream https://github.com/socon-dev/socon

#. Install ``tox``. This tool runs all the tests and will automatically
   setup a virtual environment to run the tests in::

   $ pip install tox

#. Make your changes. Do not forget to follow the :doc:`coding rules <coding-style>`

#. Run the tests + linting with tox::

   $ tox -e flake8,py39

   This command will run tests via ``tox`` tool against python 3.9 and perform
   a ``lint`` coding style check using ``flake8``

#. In case you don't want to run the tests using ``tox`` you can do it manually.
   First create a :doc:`virtual environment </intro/environment>` then go to the
   ``tests`` directory and::

      $ python -m pip install -e ..
      $ python -m pip install -r requirement/requirements.txt
      $ pytest -v

#. Add yourself to AUTHORS file if not there yet, in alphabetical order.

#. Commit and push once your tests pass and you are happy with your changes::

      $ git commit -m "#ticket-id <commit message>"
      $ git push -u

   The ticket id that you are working on must be put in the commit message
   using #ticket-id

#. Finally, submit your pull request through the GiHub website. When your
   pull request will be created, Socon will automatically tests your pull
   requests and let you know if everything is working.

Tests
=====

Socon uses `pytest`_ to write and run tests. Socon comes with a
test suite of its own, in the ``tests`` directory of the code base.
It is mandatory that all tests pass at all times.

Quick installation guide
------------------------

#. Fork the `Socon <https://github.com/socon-dev/socon>`_. If you don't know how
   to do it, check the `GitHub documentation <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`__
   documentation.

#. Create and activate a :doc:`virtual environment </intro/environment>`

#. Open Git bash, clone your fork locally using git, install the requirements
   and run the tests::

   $ git clone git@github.com:YOUR_GITHUB_USERNAME/socon.git
   $ cd socon/tests
   $ python -m pip install -e ..
   $ python -m pip install -r requirement/requirements.txt
   $ pytest -v

Writing tests
-------------

When you write a test, we would love for you to follow couple rules:

* Write tests before you write your functionality (TDD). Test-drive development.
   Write a test, make it run, change the code to make it right, repeat the process.

* Keep tests short. It's easier to read and understand.

* Use pytest fixture and don't repeat yourself.

* Test one requirement at a time.

* Look at what has been done before and use as example.

Code coverage
-------------

Socon should always be 100% covered. We encourage developers to always look
if their changes are covered by tests. Coverage doesn't mean that there
are no bugs but it helps build confidence in the project.

If you installed the above requirement, ``cd`` into Socon root directory and::

   $ pytest --cov-report html --cov=socon tests/

This command will generate an html report in a ``coverage`` directory. From
there you can check the ``index.html``. This page display Socon coverage
by modules.

.. _pytest: https://github.com/pytest-dev/pytest
