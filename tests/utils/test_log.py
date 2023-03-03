import pytest

from socon import setup
from socon.test.utils import override_settings


def dictConfig(config):
    dictConfig.called = True


@pytest.mark.parametrize(
    "logging, result", (("utils.test_log.dictConfig", True), ("", False))
)
def test_configure_initializes_logging(logging, result):
    dictConfig.called = False
    try:
        with override_settings(
            LOGGING_CONFIG=logging,
        ):
            setup()
    finally:
        # Restore logging from settings.
        setup()
    assert dictConfig.called is result
