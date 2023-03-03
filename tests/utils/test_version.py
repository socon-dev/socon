import re

from unittest import skipUnless

import pytest

import socon.utils.version

from socon.utils.version import (
    get_complete_version,
    get_docs_version,
    get_git_changeset,
    get_version,
)


class VersionTests:
    def test_development(self):
        """Check development version generation"""
        ver_tuple = (1, 4, 0, "alpha", 0)
        ver_string = get_version(ver_tuple)
        assert re.match(r"1\.4(\.dev[0-9a-z]{7})?", ver_string)

    @skipUnless(
        hasattr(socon.utils.version, "__file__"),
        "test_development() checks the same when __file__ is already missing, "
        "e.g. in a frozen environments",
    )
    def test_development_no_file(self):
        get_git_changeset.cache_clear()
        version_file = socon.utils.version.__file__
        try:
            del socon.utils.version.__file__
            self.test_development()
        finally:
            socon.utils.version.__file__ = version_file

    def test_releases(self):
        """Check release version generation"""
        tuples_to_strings = (
            ((1, 4, 0, "alpha", 1), "1.4a1"),
            ((1, 4, 0, "beta", 1), "1.4b1"),
            ((1, 4, 0, "rc", 1), "1.4rc1"),
            ((1, 4, 0, "final", 0), "1.4"),
            ((1, 4, 1, "rc", 2), "1.4.1rc2"),
            ((1, 4, 1, "final", 0), "1.4.1"),
        )
        for ver_tuple, ver_string in tuples_to_strings:
            assert get_version(ver_tuple) == ver_string

    @pytest.mark.parametrize("version, output", (("alpha", "dev"), ("final", "1.4")))
    def test_check_docs_version(self, version, output):
        """Check that the docs return the correct version"""
        ver_tuple = (1, 4, 0, version, 0)
        assert get_docs_version(ver_tuple) == output

    def test_get_complete_version(self):
        """UnitTest on the get_complete_version"""
        from socon import VERSION

        assert get_complete_version() == VERSION

        # Correct version of a version tuple
        ver_tuple = (1, 4, 0, "alpha", 0)
        assert get_complete_version(ver_tuple) == ver_tuple

        # Version parameter should be of length 5 anf the fourth element
        # should be 'alpha', 'beta', 'rc', 'final'
        with pytest.raises(AssertionError):
            get_complete_version((1,))
        with pytest.raises(AssertionError):
            get_complete_version((1, 4, 0, "foo", 0))
