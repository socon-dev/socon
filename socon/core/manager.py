# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from __future__ import annotations

from collections import defaultdict
from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict, Type, Union

from socon.conf import settings
from socon.core.exceptions import (
    HookNotFound,
    ImproperlyConfigured,
    ManagerNotFound,
    ManagerNotHooked,
)
from socon.core.registry import registry

if TYPE_CHECKING:
    from socon.core.registry.config import RegistryConfig


__all__ = ["managers", "BaseManager", "Hook"]


class ManagerRegistry:
    """Base class that registers all managers"""

    def __init__(self) -> None:
        self.managers: Dict[str, Type[BaseManager]] = {}

    def get_manager(self, name: str) -> Type[BaseManager]:
        """Return the manager with the given name"""
        try:
            return self.managers[name]
        except KeyError:
            raise ManagerNotFound(
                "'{}' does not exist. Choices are:\n{}".format(
                    name, list(self.managers.keys())
                )
            )

    def get_managers(self) -> list[Type[BaseManager]]:
        """Return a list of all defined managers"""
        return self.managers.values()

    def add_manager(self, manager: Type[BaseManager]):
        """Add a manager to the registry"""
        name = manager.name
        if name in self.managers:
            raise ImproperlyConfigured(
                "Manager names aren't unique. Duplicates:\n{}".format(name)
            )
        self.managers[name] = manager


# Declared here to avoid import recursion. As Hook and BaseManager
# depend on the registry, putting them in different files increase the
# import complexity.
managers = ManagerRegistry()

# -------------------------------- Base class -------------------------------- #


class Hook:
    """
    The base class from which all managers will derive from.

    By subclassing your class from the BaseManager and by explicitly
    placing your class into `managers.py` in a plugin, project or in the common
    config will auto-register the class as a manager.

    When a manager is defined, it requires to be hooked to :class:`Hook` subclass.
    """

    # The manager the hook class will be linked to
    manager: str = None

    def __init_subclass__(cls, abstract: bool = False) -> None:
        # If the class is abstract, we don't register it
        if getattr(cls, "abstract", abstract):
            return

        # If the base class has not been linked to a registry, we raise
        # an error as we won't be able to register the subclass
        if cls.manager is None:
            raise ImproperlyConfigured(
                "{} hook must be linked to a manager".format(cls.__name__)
            )

        # Get the manager for this hook
        manager = managers.get_manager(cls.manager)

        # Start registering the subclass to the main registry. First required
        # things is to find the registry config that hold the subclass
        module = cls.__module__

        config = registry.get_containing_registry_config(module)
        if config is None:
            raise RuntimeError(
                "{} class isn't in a project, plugin or in the common config. "
                "Check the INSTALLED_PROJECTS, INSTALLED_PLUGINS or the "
                "common config '{}'".format(
                    cls.__name__, settings.get_settings_module_name()
                )
            )

        manager.add_hook_impl(config, cls)


class BaseManager:
    """Main class to register manager registry

    By subclassing your class from the BaseManager and by explicitly
    placing your class into `managers.py` in a plugin, project or in the common
    config will auto-register the class as as manager. However,
    this class will require that you define two mandatory attribute.

        1. name: The name of the manager
        2. lookup_module: The module where we will find hooks to
            link to this manager

    When a manager is defined, it requires to be hooked to a Hook subclass.
    """

    # Name of the manager
    name: str = None

    # Name of the module the manager will into to import hooks.
    lookup_module: str = None

    def __init__(self) -> None:
        self.hooks = defaultdict(lambda: defaultdict(dict))
        self._imported_configs = []

    def __init_subclass__(cls, name: str = None, lookup: str = None) -> None:
        # Check the manadatory attributes
        cls.name = cls._get_mandatory_attr("name", name)
        cls.lookup_module = cls._get_mandatory_attr("lookup_module", lookup)

        # Register the manager in the managers registry
        managers.add_manager(cls())

    @classmethod
    def _get_mandatory_attr(cls, attr: str, default: Any = None) -> Any:
        cls_attr = getattr(cls, attr)
        value = cls_attr if cls_attr is not None else default
        if value is None:
            raise ImproperlyConfigured(
                "'{}' must supply a {} attribute".format(cls.__name__, attr)
            )
        return value

    def is_hooked(self) -> None:
        """Raise an exception if the manager does not contain any hooks"""
        if not self.hooks:
            raise ManagerNotHooked(
                "'{}' does not contain any hooks implementation".format(self.name)
            )
        return True

    def get_modules(self, config: Type[RegistryConfig]) -> Union[list, str]:
        """Return a list of modules to be imported"""
        return "{}.{}".format(config.name, self.lookup_module)

    def find_all(self) -> Type[Hook]:
        """
        Look into each installed registry config for hooks. This method
        import all modules returned by :meth:`BaseManager.get_modules`. When
        a module is imported, it auto-register every hook in that module.
        """
        # Find core config hooks manager
        core_config = registry.get_socon_common_config()
        self.find_hooks_impl(core_config)

        # In any case if the settings are not configured we can't continue.
        # This is because common, projects and plugins config cannot be
        # registered if the settings is not ready or has error
        if not settings.configured:
            return self

        # Check in the common config
        common_config = registry.get_user_common_config()
        self.find_hooks_impl(common_config)

        # Check in every plugins and projects
        for user_config in registry.get_user_configs():
            self.find_hooks_impl(user_config)

        return self

    def find_hooks_impl(self, config: Union[Type[RegistryConfig], None]) -> None:
        """
        Look into a specific registry config for hooks. This method import all
        modules return by :meth:`BaseManager.get_modules` for that specific config.
        """
        if config is not None:
            if config.label in self._imported_configs:
                return
            self._imported_configs.append(config.label)
            modules = self.get_modules(config)
            if isinstance(modules, str):
                modules = [modules]
            for module in modules:
                # This will trigger the __init_subclass__ of BaseManager
                try:
                    import_module(module)
                except ModuleNotFoundError:
                    pass

    def get_hooks(self, config: Type[RegistryConfig]) -> list[Type[Hook]]:
        """Return all hooks of a specific registry config"""
        self.is_hooked()
        hooks = []
        registry_config = self.hooks[config.registry.name]
        for hook in registry_config.get(config.label, {}).values():
            hooks.append(hook)
        return hooks

    def get_hook(
        self, config: Type[RegistryConfig], name: str
    ) -> Union[Type[Hook], None]:
        """Return a hook of a specific registry config"""
        self.is_hooked()
        for hook in self.get_hooks(config):
            if hook.name == name:
                return hook
        return None

    def get_hook_config_holders(self, name: str) -> list[str]:
        """Return a list of config labels that hold a specific hook"""
        self.is_hooked()
        holders = []
        for conf in self.hooks.values():
            for conf_label, hooks in conf.items():
                if name in hooks:
                    holders.append(conf_label)
        return holders

    def search_hook_impl(
        self, name: str, config: Type[RegistryConfig] = None
    ) -> Type[Hook]:
        """
        Search for a hook globally or for a specific registry config. The search
        is done following a specific order:

            #. Did the user pass a config object?
                Yes, search the hook for that config. It is found return it
                else continue.

            #. Search in the common space config for hooks.
                If it's found return it else continue.

            #. Search in the plugins.
                If it's found return it else continue.

            #. Search in built-in Socon hooks.
                if it's found return it else continue.

            #. Raise :exc:`socon.core.exceptions.HookNotFound`.
        """
        self.is_hooked()
        if config:
            hook = self.get_hook(config, name)
            if hook is not None:
                return hook

        configs = []
        if settings.configured:
            # Place common and then plugins at first in the config list. This
            # is important as we first want to look in the user common place,
            # the plugins and finally in socon core module.
            user_settings = registry.get_user_common_config()
            if user_settings:
                configs.append(user_settings)
            configs.extend(registry.plugins.get_registry_configs())

        # Always append at the end the socon common config. It's the last
        # place where we want to look at
        configs.append(registry.get_socon_common_config())

        # Iterate over all configs to find the right hook
        for config in configs:
            hook = self.get_hook(config, name)
            if hook is not None:
                return hook

        # We didn't find any hook with this name
        raise HookNotFound(
            "'{}' hook was not found in '{}' manager".format(name, self.name)
        )

    def get_hooks_name(self) -> list[str]:
        """Return a list of all registered hooks name"""
        self.is_hooked()
        names = []
        for config in self.hooks.values():
            for hooks in config.values():
                names.extend(list(hooks.keys()))
        return list(set(names))

    def add_hook_impl(self, config: Type[RegistryConfig], hook: type) -> None:
        """
        Add a hook to the manager. This function is automatically
        called from the __init_subclass__ of the hooked subclass
        """
        # Check if the command module has a name attribute. If it's
        # the case, we will use the name of the class
        hook_name = getattr(hook, "name", hook.__name__)

        # Get the config registry name. This is to categorize the commands
        # and avoid raising an error if two different config have the same
        # name in two different registry
        configs = self.hooks[config.registry.name]

        # Save in the registry the config label associated with
        # the label of the hook and its class. If the label already
        # exist we raise an ImportError
        if any(hook_name == n for n in configs.get(config.label, [])):
            raise ImproperlyConfigured(
                "'{}' already exists. Duplicates:\n{}".format(hook_name, configs)
            )

        # Save the hook to a specific config
        configs[config.label].update({hook_name: hook})
