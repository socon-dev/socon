from importlib import import_module

import pytest

from socon.core.exceptions import (
    HookNotFound,
    ImproperlyConfigured,
    ManagerNotFound,
    ManagerNotHooked,
)
from socon.core.manager import BaseManager
from socon.core.registry import projects
from socon.test import override_settings


@pytest.fixture(scope="module")
def manager_config():
    yield projects.get_registry_config("manager")


@pytest.fixture(scope="class")
def default_reg():
    default_registry = BaseManager.get_manager("default")
    yield default_registry


class BaseManagerTests:
    def test_hook_is_linked(self):
        """Check that we register only hook implementation with a manager"""
        msg = "NotLinkedToManager hook must be linked to a manager"
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(INSTALLED_PROJECTS=["manager.hook_not_linked"]):
                pass

    @override_settings(INSTALLED_PROJECTS=["manager.manager_with_abstract"])
    def test_register_only_no_abstract_hook(self, default_reg):
        """abstract hook should not be register"""
        config = projects.get_registry_config("manager_with_abstract")
        default_reg.find_hooks_impl(config)
        assert default_reg.get_hook(config, "will_be_register") is not None
        assert default_reg.get_hook(config, "abstract") is None

    def test_register_manager_outside_any_registry_config(self):
        """
        Raise an error if a hook is imported from outside a
        registry config
        """
        with override_settings(INSTALLED_PROJECTS=["registry"]):
            with pytest.raises(RuntimeError):
                import_module("manager.outside_project.lookup")


class RegistryManagerTests:
    def test_mandatory_attribute(self):
        """
        Raise an error if the manager does not contain
        a name or a lookup_module
        """
        msg = "'FooManager' must supply a lookup_module attribute"
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(INSTALLED_PROJECTS=["manager.missing_attr"]):
                pass

    def test_duplicate_manager(self):
        """There should not be duplicate manager"""
        msg = "Manager names aren't unique. Duplicates:\nfoo"
        with pytest.raises(ImproperlyConfigured, match=msg):
            with override_settings(INSTALLED_PROJECTS=["manager.duplicate_managers"]):
                pass

    def test_get_manager(self):
        """Get an imported manager from a registry config"""
        default_manager = BaseManager.get_manager("default")
        assert default_manager is not None
        assert default_manager.name == "default"

    def test_check_if_manager_is_hooked(self):
        """Raise an error if the manager does not contain any hooks"""
        # By default the manager is not linked
        msg = "'not_hooked_manager' does not contain any hooks implementation"
        with override_settings(INSTALLED_PROJECTS=["manager.manager_not_hooked"]):
            default_manager = BaseManager.get_manager("not_hooked_manager")
            with pytest.raises(ManagerNotHooked, match=msg):
                default_manager.is_hooked()
            import_module("manager.manager_not_hooked.not_hooked")
            assert default_manager.hooks

    def test_find_hooks_impl_of_a_config(self, manager_config, default_reg):
        """Check that hooks of a specific config are well imported"""
        default_reg.find_hooks_impl(manager_config)
        foo_hook = default_reg.get_hook(manager_config, "foo")
        assert foo_hook.name == "foo"

    def test_get_hooks(self, manager_config, default_reg):
        """
        Check that we can succesfully get all hooks or only one for
        a specific registry config
        """
        # Get all managers
        default_reg.find_hooks_impl(manager_config)
        hooks = default_reg.get_hooks(manager_config)
        hooks_name = [hook.name for hook in hooks]
        assert "foo" in hooks_name
        assert "bar" in hooks_name

        # Get a single manager that exist
        hook = default_reg.get_hook(manager_config, "foo")
        assert hook is not None
        assert hook.name == "foo"

        # Get a manager that does not exist
        hook = default_reg.get_hook(manager_config, "test")
        assert hook is None

    def test_search_hook_impl(self, manager_config, default_reg):
        """
        Check that we can successfully find a hook by giving or not
        a registry config. This is different from get_hook as it will
        check in every config following a specific hierarchy
        """
        default_reg.find_all()
        # With no config given, the manager that will be taken is the common
        # one. To get the one from register we need to pass the config
        manager = default_reg.search_hook_impl("foo")
        manager_instance = manager()
        assert manager_instance.execute() == "Execute from common"

        # Get the same manager from the register config
        manager = default_reg.search_hook_impl("foo", manager_config)
        manager_instance = manager()
        assert manager_instance.execute() == "Execute from manager"

        # The config exist but it does not contain the hook. If that
        # is the case we continue to search in the other config registry. If
        # not found it will raise a HookNotFound
        msg = "'will_not_exist' hook was not found in 'default' manager"
        with pytest.raises(HookNotFound, match=msg):
            manager = default_reg.search_hook_impl("will_not_exist", manager_config)

    def test_get_all_hooks_name(self, default_reg):
        """Check that we return a full list of all name without duplicate"""
        manager = default_reg.find_all()
        assert manager.get_hooks_name().sort() == ["bar", "foo"].sort()

    def test_add_hook_with_duplicate(self, default_reg):
        """Raise an error if we already register a hook with the same name"""
        with pytest.raises(ImproperlyConfigured):
            with override_settings(INSTALLED_PROJECTS=["manager.duplicate_hooks"]):
                config = projects.get_registry_config("duplicate_hooks")
                default_reg.find_hooks_impl(config)

    def test_get_manager_that_does_not_exist(self):
        """Try to get a manager that does not exist"""
        msg = "'not_exist' does not exist. Choices are:"
        with pytest.raises(ManagerNotFound, match="{}*".format(msg)):
            BaseManager.get_manager("not_exist")
