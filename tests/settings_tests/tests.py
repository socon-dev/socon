import copy
import os
import re

from types import SimpleNamespace

import pytest

from socon.conf import (
    ENVIRONMENT_VARIABLE,
    CoreSettings,
    LazySettings,
    Settings,
    global_settings,
    settings,
)
from socon.core.exceptions import ImproperlyConfigured
from socon.test.utils import override_settings


class SettingsTests:
    def test_override(self):
        settings.TEST = "test"
        assert "test" == settings.TEST
        with override_settings(TEST="override"):
            assert "override" == settings.TEST
        assert "test" == settings.TEST
        del settings.TEST

    def test_override_change(self):
        settings.TEST = "test"
        assert "test" == settings.TEST
        with override_settings(TEST="override"):
            assert "override" == settings.TEST
            settings.TEST = "test2"
        assert "test" == settings.TEST
        del settings.TEST

    def test_override_doesnt_leak(self):
        with pytest.raises(AttributeError):
            getattr(settings, "TEST")
        with override_settings(TEST="override"):
            assert "override" == settings.TEST
            settings.TEST = "test"
        with pytest.raises(AttributeError):
            getattr(settings, "TEST")

    @override_settings(TEST="override")
    def test_decorator(self):
        assert "override" == settings.TEST

    def test_context_manager(self):
        with pytest.raises(AttributeError):
            getattr(settings, "TEST")
        override = override_settings(TEST="override")
        with pytest.raises(AttributeError):
            getattr(settings, "TEST")
        with override:
            assert "override" == settings.TEST
        with pytest.raises(AttributeError):
            getattr(settings, "TEST")

    def test_settings_delete(self):
        settings.TEST = "test"
        assert "test" == settings.TEST
        del settings.TEST
        msg = "'Settings' object has no attribute 'TEST'"
        with pytest.raises(AttributeError, match=msg):
            getattr(settings, "TEST")

    def test_settings_delete_wrapped(self):
        with pytest.raises(TypeError, match="can't delete _wrapped."):
            delattr(settings, "_wrapped")

    def test_override_settings_delete(self):
        """
        Allow deletion of a setting in an overridden settings set (#18824)
        """
        previous_ad = settings.LOGGING
        with override_settings(LOGGING="TEST"):
            del settings.LOGGING
            del settings.NOT_EXIST
            with pytest.raises(AttributeError):
                getattr(settings, "LOGGING")
            with pytest.raises(AttributeError):
                getattr(settings, "NOT_EXIST")
            assert "LOGGING" not in dir(settings)
        assert settings.LOGGING == previous_ad

    def test_override_settings_nested(self):
        """
        override_settings uses the actual _wrapped attribute at
        runtime, not when it was instantiated.
        """

        with pytest.raises(AttributeError):
            getattr(settings, "TEST")
        with pytest.raises(AttributeError):
            getattr(settings, "TEST2")

        inner = override_settings(TEST2="override")
        with override_settings(TEST="override"):
            assert "override" == settings.TEST
            with inner:
                assert "override" == settings.TEST
                assert "override" == settings.TEST2
            # inner's __exit__ should have restored the settings of the outer
            # context manager, not these when the class was instantiated
            assert "override" == settings.TEST
            with pytest.raises(AttributeError):
                getattr(settings, "TEST2")

        with pytest.raises(AttributeError):
            getattr(settings, "TEST")
        with pytest.raises(AttributeError):
            getattr(settings, "TEST2")

    def test_default_no_settings_module(self):
        """Check default raise error if user provide a not existing settings
        module"""

        class TestSettings(LazySettings):
            def _get_settings(self) -> str:
                return None

        test_settings = TestSettings()
        msg = "Requested setting TEST, but settings are not configured."
        with pytest.raises(ImproperlyConfigured, match=msg):
            test_settings.TEST

    def test_no_settings_module(self):
        """Test no settings module defined or found by CoreSettings"""
        msg = (
            "Requested setting{}, but settings are not configured. You "
            "must either define the environment variable SOCON_SETTINGS_MODULE "
            "or call settings.configure() before accessing settings."
        )
        orig_settings = os.environ[ENVIRONMENT_VARIABLE]
        os.environ[ENVIRONMENT_VARIABLE] = ""
        try:
            with pytest.raises(ImproperlyConfigured, match=re.escape(msg.format("s"))):
                settings._setup()
            with pytest.raises(
                ImproperlyConfigured, match=re.escape(msg.format(" TEST"))
            ):
                settings._setup("TEST")
        finally:
            os.environ[ENVIRONMENT_VARIABLE] = orig_settings

    def test_already_configured(self):
        """Check that an error is raised If we try to configure an already
        configured settings"""
        with pytest.raises(RuntimeError, match="Settings already configured."):
            settings.configure("")

    def test_nonupper_settings_prohibited_in_configure(self):
        """Configure accept only uppercase variable"""
        s = CoreSettings()
        with pytest.raises(TypeError, match="Setting 'foo' must be uppercase."):
            s.configure(SimpleNamespace(), foo="bar")

    def test_nonupper_settings_in_settings_class(self):
        """Check that Settings class register only uppercase"""
        s = Settings("settings_tests.test_settings")
        s._load_settings()
        with pytest.raises(AttributeError):
            s.foo
        assert s.BAR == "foo"

    def test_get_settings_not_implemented(self):
        """Check that _get_settings is implemented"""

        class TestSettings(LazySettings):
            pass

        test_settings = TestSettings()
        with pytest.raises(NotImplementedError):
            test_settings._setup()

    def test_setattr_settings_not_ready(self):
        """Check that _setup() is called when we set an attribute"""
        test_settings = CoreSettings()
        test_settings.TEST = "a"
        assert test_settings.TEST == "a"

    def test_delattr_settings_not_ready(self):
        """Check that _setup() is called when we delete an attribute"""
        test_settings = CoreSettings()
        with pytest.raises(AttributeError):
            del test_settings.TEST

    def test_copy_settings(self):
        """Test copy and deepcopy on initialize or no-initialize settings"""
        # Test a simple copy
        settings.TEST = ["test"]
        new_settings = copy.copy(settings)
        new_settings.TEST.append("other")
        assert new_settings.LOGGING_CONFIG == "logging.config.dictConfig"
        assert settings.TEST == ["test", "other"]

        # Test deepcopy
        new_settings = copy.deepcopy(settings)
        new_settings.TEST.append("another")
        assert settings.TEST == ["test", "other"]
        assert new_settings.TEST == ["test", "other", "another"]
        del settings.TEST

        # Test copy and deepcopy on not initialized settings
        s = CoreSettings()
        copy_settings = copy.copy(s)
        deepcopy_settings = copy.deepcopy(s)
        assert copy_settings.configured is False
        assert deepcopy_settings.configured is False

    def test_get_core_settings_module(self):
        """Get the settings module for the CoreSettings"""
        s = CoreSettings()
        assert s.get_settings_module_name() is None
        s._setup()
        assert s.get_settings_module_name() == "common"


class IsOverriddenTests:
    def test_override(self):
        assert (settings.is_overridden("OVERRIDE")) is False
        with override_settings(OVERRIDE=[]):
            assert (settings.is_overridden("OVERRIDE")) is True
        s = LazySettings()
        s.configure(SimpleNamespace(BAR="foo"))
        assert s.is_overridden("BAR") is False

    def test_unevaluated_lazysettings_repr(self):
        lazy_settings = LazySettings()
        expected = "<LazySettings [Unevaluated]>"
        assert repr(lazy_settings) == expected

    def test_evaluated_lazysettings_repr(self):
        lazy_settings = CoreSettings()
        module = os.environ.get(ENVIRONMENT_VARIABLE)
        expected = '<LazySettings "%s">' % module
        # Force evaluation of the lazy object.
        lazy_settings.LOGGING
        assert repr(lazy_settings) == expected

    def test_usersettingsholder_repr(self):
        lazy_settings = LazySettings()
        lazy_settings.configure(global_settings, APPEND_SLASH=False)
        expected = "<UserSettingsHolder>"
        assert repr(lazy_settings._wrapped) == expected

    def test_settings_repr(self):
        module = os.environ.get(ENVIRONMENT_VARIABLE)
        lazy_settings = Settings(module)
        expected = '<Settings "%s">' % module
        assert repr(lazy_settings) == expected

    def test_settings_setup_on_dir_call(self):
        """setup the settings on __dir__ call"""
        s = CoreSettings()
        assert "LOGGING" in dir(s)
