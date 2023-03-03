from importlib import import_module

import pytest

from socon.utils.module_loading import import_string, module_has_submodule


class ModuleHasSubmoduleTests:
    @pytest.fixture
    def test_module(self):
        yield import_module("utils.test_module")

    def test_loader_default_module(self, test_module):
        # An importable child
        assert module_has_submodule(test_module, "good_module") is True
        mod = import_module("utils.test_module.good_module")
        assert mod.content == "Good Module"

        # A child that exists, but will generate an import error if loaded
        assert module_has_submodule(test_module, "bad_module") is True
        with pytest.raises(ImportError):
            import_module("utils.test_module.bad_module")

        # A child that doesn't exist
        assert module_has_submodule(test_module, "no_such_module") is False
        with pytest.raises(ImportError):
            import_module("utils.test_module.no_such_module")

        # A child that doesn't exist, but is the name of a package on the path
        assert module_has_submodule(test_module, "socon") is False
        with pytest.raises(ImportError):
            import_module("utils.test_module.socon")

    def test_has_sumbodule_with_dotted_path(self, test_module):
        """Nested module existence can be tested."""

        # A grandchild that exists.
        assert (
            module_has_submodule(test_module, "child_module.grandchild_module") is True
        )

        # A grandchild that doesn't exist.
        assert module_has_submodule(test_module, "child_module.no_such_module") is False

        # A grandchild whose parent doesn't exist.
        assert (
            module_has_submodule(test_module, "no_such_module.grandchild_module")
            is False
        )

        # A grandchild whose parent is not a package.
        assert module_has_submodule(test_module, "good_module.no_such_module") is False


class ModuleImportTests:
    def test_import_string(self):
        cls = import_string("socon.utils.module_loading.import_string")
        assert cls == import_string

        # Test exceptions raised
        with pytest.raises(ImportError):
            import_string("no_dots_in_path")

        # Test ImportError on attribute non existing in module
        msg = 'Module "utils" does not define a "unexistent" attribute'
        with pytest.raises(ImportError, match=msg):
            import_string("utils.unexistent")
