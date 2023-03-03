To run the test suite, first, create and activate a virtual environment.
For whom that doesn't know how to do that, read ``docs/intro/environment.txt``

Install some requirements in your virtual env and run the tests::

    $ cd tests
    $ python -m pip install -e ..
    $ python -m pip install -r requirement/requirements.txt
    $ pytest -v

You can also run the tests using ``tox``. The tool will automatically create
an environment to build and test Socon. To install ``tox`` and run the tests::

    $ pip install -e tox
    $ tox -e py39
