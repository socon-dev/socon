=====
Socon
=====

.. image:: https://img.shields.io/badge/python-3.9-blue.svg
    :target: https://github.com/socon-dev/socon

.. image:: https://github.com/socon-dev/socon/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/socon-dev/socon/actions?query=workflow%3APython%20testing

.. image:: https://codecov.io/gh/socon-dev/socon/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/socon-dev/socon
    :alt: Code coverage Status

.. image:: https://github.com/socon-dev/socon/actions/workflows/linters.yml/badge.svg
    :target: https://github.com/socon-dev/socon/actions?query=workflow%3APython%20linting

.. image:: https://readthedocs.org/projects/socon/badge/?version=latest
    :target: https://socon.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Socon is a high-level Python framework that helps you develop a generic and
robust framework for your different projects. Let us forget about
writing hundred of scripts with thousands of configurations, this framework
will help your organize your work and will speed your development.

Socon's create a generic Django like project structure. It's a structure that contains
all the element for you to get started with your framework and all
your different projects.

Why Socon ?
===========

I believe we have all ended-up in a situation where we have had multiple
projects that need to share the same scripts or components. Some projects may need a
specific configuration or a specific function to be executed. Also, we often
spend a great amount of time writing a script that is not generic enough to be used by
all of our different projects.

Socon has been designed to simplify all that. Socon works with commands.
Socon will let you define common commands that can be shared across projects.
Each project can either write their own commands, or override common commands
to change their behaviors by adding or removing functionalities.

The framework also provide features like managers and hooks. These features will
allow you to increase the functionalities of your framework while maintaining
genericity accross your different projects.

Documentation
=============

The full documentation is in the "``docs``" directory on `GitHub`_ or online at
https://socon.readthedocs.io/en/latest/

If you are just getting started, We recommend that you read the documentation in this
order:

* Read ``docs/intro/install.txt`` for instructions on how to install Socon.

* Walk through each tutorial in numerical order: ``docs/intro/tutorials``

* Jump to the ``docs/how-to`` for specific problems and use-cases.

* Checkout the ``docs/ref`` for more details about API's and functionalities.

Check ``docs/README`` for instructions on building an HTML version of the docs.

Example
=======

Let's imagine that you have two different projects. One project called ``artemis``
and the other one ``apollo``. Both of these NASA projects need to launch a different
rocket.

There are two possibilities:

* Write a different scripts for each project but you lose the genericity.

* Or write a generic script that will load a configuration file with
  the information of both rockets and the launch procedure.
  This will be the best solution, but it will be time consuming
  and might not take into account all the possibilities.

Socon was created to facilitate the second method. You are able to create common
commands that are available to all projects you have created
using the ``createproject`` command.

.. code-block:: python

    from socon.core.management.base import ProjectCommand, Config
    from socon.core.registry.base import ProjectConfig


    class LaunchCommand(ProjectCommand):
        name = 'launch'

        def handle(self, config: Config, project_config: ProjectConfig):
            spacecraft = project_config.get_setting('SPACECRAFT')
            print(f'Launching the {spacecraft} SpaceCraft to the moon')

This command is declared in the common space of your framework created by the
``createcontainer`` command.

We are using a project_config object to load the name of the spacecraft.
This project_config object is loaded when you start the command and you specify the
project.

The ``SPACECRAFT`` variable is stored in a file called ``config.py`` at the root of
every project created by the command ``createproject``.

.. code-block:: python

    # Artemis config.py
    SPACECRAFT = 'Artemis 1'

.. code-block:: python

    # Apollo config.py
    SPACECRAFT = 'Saturn V'

Now that everything is setup. You can just run the following:

.. code-block:: console

    $ python manage.py launch --project artemis
    $ Launching the Artemis 1 SpaceCraft the the moon

    $ python manage.py launch --project apollo
    $ Launching the Saturn V SpaceCraft the the moon

Of course the framework capabilities do not stop here. You can go even further,
for example by redefining functionalities of the launch command.

We invite you to walk through each tutorial in numerical
order here: ``docs/intro/tutorials``


Contribution
============

Anyone can contribute to Socon's development. Checkout our documentation
on how to get involved: `https://socon.readthedocs.io/en/latest/internals/contributing.html`

This is a one man show for now, send help!

License
=======

Copyright Stephane Capponi and others, 2023
Distributed under the terms of the BSD-3-Clause license, socon is free and
open source software.

Socon also reused codes from third-paty. You can find the licenses of these
third-paty in the `licenses`_ folder. Each files that has been reused and
modified contains an SPDX section to specify the license used and the Copyright.
If you want more information about our licence and why we reused code
from third-paty, check the ``docs/intro/overview.txt``

.. _licenses: https://github.com/socon-dev/socon/tree/master/licenses
.. _GitHub: https://github.com/socon-dev/socon/
