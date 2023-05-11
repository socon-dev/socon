import os
import re

from unittest import mock

import pytest

from socon.core.exceptions import ImproperlyConfigured, RegistryNotReady
from socon.core.manager import managers
from socon.core.registry import projects, registry
from socon.core.registry.base import BaseRegistry
from socon.core.registry.config import ProjectConfig, RegistryConfig
from socon.test.utils import override_settings

from .one_config_project.projects import OneConfig

ONE_CONFIG = ["registry.one_config_project"]

TWO_CONFIGS = ["registry.two_configs_env"]

TEST_INSTALLED_PROJECTS = ["registry.default_config"]


class BaseRegistryTests:
    @pytest.fixture(autouse=True)
    def registry(self):
        yield BaseRegistry("test", None)

    def test_registry_get_single_name(self, registry):
        assert registry.single_registry_name == "test"
        registry.name = "tests"
        assert registry.single_registry_name == "test"

    def test_populate_with_config_class(self, registry):
        config = RegistryConfig.create("registry.registry_config")
        registry.populate([config])
        assert registry.registry_ready is True
        assert len(registry.registry_configs) == 1


class ProjectsTests:
    """
    Project registry tests. This validate most of all functionality
    of BaseRegistry
    """

    def test_ready(self):
        """
        Tests the ready property of the master registry.
        """
        # The master project registry is always ready when the tests run.
        assert projects.registry_ready is True
        # Non-master project registries are populated in __init__.
        assert BaseRegistry("base").registry_ready is True

    def test_project_is_installed(self):
        assert projects.is_installed("registry") is True
        assert projects.is_installed("foo") is False

    def test_bad_project_config(self):
        """
        Tests when INSTALLED_PROJECTS contains an incorrect app config.
        """
        bad_config = "registry.default_config.projects.BadConfig"
        msg = "'{}' must supply a name attribute.".format(bad_config)
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(
                INSTALLED_PROJECTS=[bad_config], SKIP_ERROR_ON_PROJECTS_IMPORT=False
            ):
                pass

    def test_no_such_project(self):
        """
        Tests when INSTALLED_PROJECTS contains an app that doesn't exist, either
        directly or via an app config.
        """
        with pytest.raises(ImportError):
            with override_settings(
                INSTALLED_PROJECTS=["there is no such project"],
                SKIP_ERROR_ON_PROJECTS_IMPORT=False,
            ):
                pass
        msg = (
            "Cannot import 'there is no such project'. "
            "Check that 'registry.default_config.projects.NoSuchProject.name' is correct."
        )
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(
                INSTALLED_PROJECTS=["registry.default_config.projects.NoSuchProject"],
                SKIP_ERROR_ON_PROJECTS_IMPORT=False,
            ):
                pass

    def test_no_such_project_config(self):
        msg = "Module 'registry' does not contain a 'NoSuchConfig' class."
        with pytest.raises(ImportError, match=msg):
            with override_settings(
                INSTALLED_PROJECTS=["registry.NoSuchConfig"],
                SKIP_ERROR_ON_PROJECTS_IMPORT=False,
            ):
                pass

    def test_not_a_project_config(self):
        """
        Tests when INSTALLED_PROJECTS contains a class that isn't an project config.
        """
        msg = "'registry.default_config.projects.NotAConfig' isn't a subclass of ProjectConfig."
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(
                INSTALLED_PROJECTS=["registry.default_config.projects.NotAConfig"],
                SKIP_ERROR_ON_PROJECTS_IMPORT=False,
            ):
                pass

    def test_no_such_project_config_with_choices(self):
        msg = (
            "Module 'registry.default_config.projects' does not contain a 'NoSuchConfig' class. "
            "Choices are: 'BadConfig', 'NoSuchProject', 'PlainProjectsConfig', "
            "'RelabeledProjectsConfig'"
        )
        with pytest.raises(ImportError, match=msg):
            with override_settings(
                INSTALLED_PROJECTS=["registry.default_config.projects.NoSuchConfig"],
                SKIP_ERROR_ON_PROJECTS_IMPORT=False,
            ):
                pass

    @override_settings(
        INSTALLED_PROJECTS=["registry.default_config.projects.NoSuchProject"]
    )
    def test_unregistered_project_config(self):
        msg = (
            "Cannot import 'there is no such project'. "
            "Check that 'registry.default_config.projects.NoSuchProject.name' is correct."
        )
        assert len(projects.unregistered_configs) == 1
        raised_message = projects.unregistered_configs.get(
            "registry.default_config.projects.NoSuchProject"
        )
        with pytest.raises(ImproperlyConfigured, match=msg):
            raise raised_message

    def test_no_config_project(self):
        """Load a project that doesn't provide an ProjectConfig class."""
        with override_settings(INSTALLED_PROJECTS=["registry.no_config_project"]):
            config = projects.get_registry_config("no_config_project")
        assert isinstance(config, ProjectConfig)

    def test_one_config_project(self):
        """Load a project that provides an ProjectConfig class."""
        with override_settings(INSTALLED_PROJECTS=["registry.one_config_project"]):
            config = projects.get_registry_config("one_config_project")
        assert isinstance(config, OneConfig)

    def test_two_configs_project(self):
        """Load a project that provides two ProjectConfig classes."""
        with override_settings(INSTALLED_PROJECTS=["registry.two_configs_project"]):
            config = projects.get_registry_config("two_configs_project")
        assert isinstance(config, ProjectConfig)

    @override_settings(INSTALLED_PROJECTS=TEST_INSTALLED_PROJECTS)
    def test_get_project_configs(self):
        """
        Tests projects.get_registry_configs().
        """
        project_configs = projects.get_registry_configs()
        assert [
            project_config.name for project_config in project_configs
        ] == TEST_INSTALLED_PROJECTS

    @override_settings(INSTALLED_PROJECTS=TEST_INSTALLED_PROJECTS)
    def test_get_project_config(self):
        """
        Tests projects.get_registry_config().
        """
        project_config = projects.get_registry_config("default_config")
        assert project_config.name == "registry.default_config"

        with pytest.raises(LookupError):
            projects.get_registry_config("admindocs")

        msg = (
            "No installed project with label 'registry.default_config'."
            " Did you mean 'default_config'?"
        )
        with pytest.raises(LookupError, match=msg):
            projects.get_registry_config("registry.default_config")

    @mock.patch.dict(
        os.environ, {"SOCON_ACTIVE_PROJECT": "one_config_project"}, clear=True
    )
    @override_settings(INSTALLED_PROJECTS=ONE_CONFIG)
    def test_get_project_config_by_env(self):
        """
        Tests projects.get_registry_config().
        """
        project_config = projects.get_project_config_by_env()
        assert isinstance(project_config, OneConfig)

    @override_settings(INSTALLED_PROJECTS=ONE_CONFIG)
    def test_cannot_get_project_config_by_env(self):
        """Raise LookupError if we can't find a project_config"""
        msg = (
            "Cannot autodetect any project. You can find below the list "
            "of the available projects:\n"
            "{}".format([p.label for p in projects.get_registry_configs()])
        )
        with pytest.raises(LookupError, match=re.escape(msg)):
            projects.get_project_config_by_env()

    @override_settings(INSTALLED_PROJECTS=TEST_INSTALLED_PROJECTS)
    def test_is_installed(self):
        """
        Tests projects.is_installed().
        """
        assert projects.is_installed("registry.default_config") is True

    def test_duplicate_labels(self):
        with pytest.raises(
            ImproperlyConfigured, match="Project labels aren't unique.*"
        ):
            default_projects = [
                "registry.default_config.projects.PlainProjectsConfig",
                "registry.default_config.projects",
            ]
            with override_settings(INSTALLED_PROJECTS=default_projects):
                pass

    def test_duplicate_names(self):
        with pytest.raises(ImproperlyConfigured, match="Project names aren't unique"):
            default_projects = [
                "registry.default_config.projects.RelabeledProjectsConfig",
                "registry.default_config.projects",
            ]
            with override_settings(INSTALLED_PROJECTS=default_projects):
                pass

    def test_get_containing_registry_config_not_ready(self):
        """
        projects.get_containing_registry_config() should raise an exception if
        projects.registry_ready isn't True.
        """
        projects.registry_ready = False
        try:
            with pytest.raises(RegistryNotReady, match="Projects aren't loaded yet"):
                projects.get_containing_registry_config("foo")
        finally:
            projects.registry_ready = True

    @pytest.mark.parametrize(
        "config_label, config_found",
        [("registry", "registry"), ("foo", None), ("registry_foo", None)],
    )
    def test_get_containing_registry_config(self, config_label, config_found):
        registry_config = projects.get_containing_registry_config(config_label)
        if config_found is None:
            assert registry_config is None
        else:
            assert registry_config.name == config_found

    @override_settings(INSTALLED_PROJECTS=["registry.config_with_manager"])
    def test_register_registry_manager(self):
        """Check that we correctly register managers on registry config import"""
        manager = managers.get_manager("test_manager")
        assert manager is not None


class Stub:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class RegistryConfigTests:
    def test_repr(self):
        pc = RegistryConfig("label", Stub(__path__=["a"]))
        assert repr(pc) == "<RegistryConfig: label>"

    def test_path_set_explicitly(self):
        class MyConfig(RegistryConfig):
            path = "foo"

        rc = MyConfig("label", Stub())
        assert rc.path == "foo"

    def test_dunder_path(self):
        """If single element in __path__, use it (in preference to __file__)."""
        ac = RegistryConfig("label", Stub(__path__=["a"], __file__="b/__init__.py"))

        assert ac.path == "a"

    def test_no_dunder_path_fallback_to_dunder_file(self):
        """If there is no __path__ attr, use __file__."""
        ac = RegistryConfig("label", Stub(__file__="b/__init__.py"))

        assert ac.path == "b"

    def test_empty_dunder_path_fallback_to_dunder_file(self):
        """If the __path__ attr is empty, use __file__ if set."""
        ac = RegistryConfig("label", Stub(__path__=[], __file__="b/__init__.py"))

        assert ac.path == "b"

    def test_multiple_dunder_path_fallback_to_dunder_file(self):
        """If the __path__ attr is length>1, use __file__ if set."""
        ac = RegistryConfig(
            "label", Stub(__path__=["a", "b"], __file__="c/__init__.py")
        )

        assert ac.path == "c"

    def test_no_dunder_path_or_dunder_file(self):
        """If there is no __path__ or __file__, raise ImproperlyConfigured."""
        with pytest.raises(ImproperlyConfigured):
            RegistryConfig("label", Stub())

    def test_empty_dunder_path_no_dunder_file(self):
        """If the __path__ attr is empty and there is no __file__, raise."""
        with pytest.raises(ImproperlyConfigured):
            RegistryConfig("label", Stub(__path__=[]))

    def test_multiple_dunder_path_no_dunder_file(self):
        """If the __path__ attr is length>1 and there is no __file__, raise."""
        with pytest.raises(ImproperlyConfigured):
            RegistryConfig("label", Stub(__path__=["a", "b"]))


class ProjectConfigTests:
    def test_no_settings_module(self):
        """
        If settings_module is not set, we should raise an error when
        settings is accessed if management.config does not exist
        """
        pc = projects.get_registry_config("registry")
        msg = "No module named 'registry.management'"
        with pytest.raises(ImportError, match=msg):
            pc.settings.FOO

    def test_import_error_on_settings_lazy_access(self):
        """
        If we set a settings_module module that does not exist. When we
        access the settings it should raise an error
        """
        with override_settings(
            INSTALLED_PROJECTS=[
                "registry.config_with_settings.projects.ProjectWithWrongModule"
            ]
        ):
            pc = projects.get_registry_config("wrong_settings")
            msg = "No module named 'registry.config_with_settings.No settings module'"
            with pytest.raises(ImportError, match=msg):
                pc.settings.FOO

    def test_get_settings_from_settings_module(self):
        """Access a settings from the project config settings"""
        with override_settings(INSTALLED_PROJECTS=["registry.config_with_settings"]):
            pc = projects.get_registry_config("config_with_settings")
            assert pc.settings.FOO == "foo"
            assert pc.settings.BAR == "bar"

    def test_get_settings_from_define_settings_module(self):
        """Access to settings_module defined by the user"""
        with override_settings(
            INSTALLED_PROJECTS=[
                "registry.config_with_settings.projects.ProjectWithSettings"
            ]
        ):
            pc = projects.get_registry_config("other_settings")
            assert pc.settings.SUPER_SETTINGS_1 == "foo"
            assert pc.settings.SUPER_SETTINGS_2 == "bar"

    def test_get_settings_with_function_get_setting(self):
        """Use the get_setting method to access the settings"""
        with override_settings(INSTALLED_PROJECTS=["registry.config_with_settings"]):
            pc = projects.get_registry_config("config_with_settings")
            assert pc.get_setting("FOO") == "foo"
            assert pc.get_setting("BAR") == "bar"

            # Access a settings that does not exist
            msg = "TEST setting does not exist in config_with_settings project"
            with pytest.raises(ValueError, match=msg):
                pc.get_setting("TEST")

            # Access a settings that does not exist but skip error
            assert pc.get_setting("TEST", skip=True) is None

            # Set a default setting if does not exist
            assert pc.get_setting("TEST", skip=True, default="DEFAULT") == "DEFAULT"


class PluginConfigTests:
    @override_settings(INSTALLED_PLUGINS=["registry.plugins"])
    def test_plugin_is_installed(self):
        """Verify that the plugin is correctly installed"""
        assert registry.plugins.is_installed("registry.plugins") is True

    def test_plugin_installed_exception(self):
        """Raise an exception and uninstall all previously installed plugin"""
        with pytest.raises(ModuleNotFoundError):
            with override_settings(INSTALLED_PLUGINS=["registry.foo"]):
                pass


class CoreRegistryTests:
    @pytest.mark.parametrize("config_name", ("registry", "common", "socon", "foo"))
    def test_get_containing_registry_config(self, config_name):
        """Get the config by searching in every config registried"""
        config = registry.get_containing_registry_config(config_name)
        if config:
            assert config.label == config_name
        else:
            assert config is None

    def test_get_registries_by_importance_order(self):
        """Check that we get Socon registries in the correct order"""
        config_registries = registry.get_registries_by_importance_order()
        assert config_registries == ["common", "plugins", "projects"]

    @override_settings(INSTALLED_PROJECTS=["registry"])
    def test_get_all_user_configs(self):
        """Get projects and plugins defined in settings"""
        configs = registry.get_user_configs()
        # Only registry config should be present
        assert len(configs) == 1
        assert configs[0].label == "registry"

    def test_get_socon_config(self):
        """Get the Socon registry config"""
        core_config = registry.get_socon_common_config()
        assert core_config.label == "core"
        assert core_config.name == "socon.core"

    def test_get_user_common_config(self):
        """Get the common user config"""
        common_config = registry.get_user_common_config()
        assert common_config.label == "common"
        assert common_config.name == "common"
