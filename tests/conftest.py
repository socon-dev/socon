import copy
import os
import shutil
import tempfile

from pathlib import Path

import pytest

from socon.utils.log import DEFAULT_LOGGING

try:
    import socon
except ImportError as e:
    raise RuntimeError(
        "Socon module not found, reference tests/README.rst for instructions."
    ) from e
else:
    from socon.conf import settings
    from socon.core.registry import projects

# ---------------------------------------------------------------------------- #
#                             Environment variable                             #
# ---------------------------------------------------------------------------- #

# Test directory
RUNTESTS_DIR = Path(__file__).resolve().parent

# Create a specific subdirectory for the duration of the test suite.
TMPDIR = tempfile.mkdtemp(prefix="testbench_")

# Set the TMPDIR environment variable in addition to tempfile.tempdir
# so that children processes inherit it.
tempfile.tempdir = os.environ["TMPDIR"] = TMPDIR

# ---------------------------------------------------------------------------- #
#                                Setup function                                #
# ---------------------------------------------------------------------------- #


def get_test_modules():
    """Get every module test module"""
    modules = []

    for f in os.scandir(RUNTESTS_DIR):
        if (
            "." not in f.name
            and not f.is_file()
            and os.path.exists(os.path.join(f.path, "__init__.py"))
        ):
            modules.append(f.name)
    return modules


def setup(verbosity):
    if verbosity >= 1:
        msg = "Testing against Socon installed in '%s'" % os.path.dirname(
            socon.__file__
        )
        print(msg)

    state = {
        "INSTALLED_PROJECTS": settings.INSTALLED_PROJECTS,
    }

    log_config = copy.deepcopy(DEFAULT_LOGGING)
    settings.LOGGING = log_config

    # Load all the test model projects.
    test_modules = get_test_modules()

    for module_name in test_modules:
        if verbosity >= 2:
            print("Importing application %s" % module_name)
        settings.INSTALLED_PROJECTS.append(module_name)

    # Load all the modules at the root of tests as projects
    socon.setup()

    projects.set_installed_configs(settings.INSTALLED_PROJECTS)

    return state


# ---------------------------------------------------------------------------- #
#                                Pytest section                                #
# ---------------------------------------------------------------------------- #


def pytest_configure(config):
    os.environ.setdefault("SOCON_SETTINGS_MODULE", "common.settings")
    verbose = config.getoption("verbose", 1)
    config.setting_state = setup(verbose)


def pytest_unconfigure(config):
    # Restore the old settings.
    for key, value in config.setting_state.items():
        setattr(settings, key, value)
    shutil.rmtree(TMPDIR)


def pytest_addoption(parser):
    parser.addoption(
        "--settings",
        help=(
            'Python path to settings module, e.g. "myproject.settings". If '
            "this isn't provided, either the TESTBENCH_SETTINGS_MODULE "
            'environment variable or "test_settings" will be used.'
        ),
    )


# ---------------------------------------------------------------------------- #
#                                    Fixture                                   #
# ---------------------------------------------------------------------------- #


@pytest.fixture()
def test_dir():
    tmpdir = tempfile.TemporaryDirectory()
    test_dir = Path(tmpdir.name, "test_project").resolve()
    os.mkdir(test_dir)
    yield test_dir
    tmpdir.cleanup()
