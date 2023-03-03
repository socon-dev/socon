# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

from __future__ import annotations

import inspect
import os

from importlib import import_module
from typing import TYPE_CHECKING, Any, Optional, Type

from socon.conf import LazySettings
from socon.core.exceptions import ImproperlyConfigured
from socon.utils.func import get_object_attr
from socon.utils.module_loading import import_string, module_has_submodule

if TYPE_CHECKING:
    from socon.core.registry.base import BaseRegistry


MANAGER_MODULE_NAME = "managers"


class RegistryConfig:
    """The base class from which all configiguration ultimately derive"""

    # Module name to look for in the configs we want to install
    lookup_module_name = "config"

    def __init__(self, config_name: str, config_module: Any):
        # Full Python path to the registry config
        self.name = config_name

        # Root module for the config
        self.module = config_module

        # Reference to the registry that holds this RegistryConfig.
        # Set by the registry when it registers the RegistryConfig instance.
        self.registry: Type[BaseRegistry] = None

        # Last component of the Python path to the config e.g. 'admin'.
        # This value must be unique across the all configs in the registry
        if not hasattr(self, "label"):
            self.label = config_name.rpartition(".")[2]

        # Filesystem path to the config directory
        if not hasattr(self, "path"):
            self.path = self._path_from_module(config_module)

    def __repr__(self) -> str:
        return "<{}: {}>".format(self.__class__.__name__, self.name)

    def _path_from_module(self, module: Any) -> str:
        """Attempt to determine config's filesystem path from its module."""
        # Convert paths to list because Python's _NamespacePath doesn't support
        # indexing.
        paths = list(getattr(module, "__path__", []))
        if len(paths) != 1:
            filename = getattr(module, "__file__", None)
            if filename is not None:
                paths = [os.path.dirname(filename)]
            else:
                # For unknown reasons, sometimes the list returned by __path__
                # contains duplicates that must be removed.
                paths = list(set(paths))
        if len(paths) > 1:
            raise ImproperlyConfigured(
                "The config module {} has multiple filesystem locations ({}); "
                "you must configure this config with a {} subclass "
                "with a 'path' class attribute.".format(
                    module, paths, self.__class__.__name__
                )
            )
        elif not paths:
            raise ImproperlyConfigured(
                "The config module {} has no filesystem location, "
                "you must configure this config with a {} subclass "
                "with a 'path' class attribute.".format(module, self.__class__.__name__)
            )
        return paths[0]

    @property
    def package(self):
        """Return the name of the package the configuration is within"""
        try:
            self.module.__name__
            self.module.__path__
        except AttributeError:
            return self.name.removesuffix(".{}".format(self.lookup_module_name))
        return self.name

    @classmethod
    def create(cls, entry: str) -> RegistryConfig:
        """Factory that creates a registry config from an entry."""
        # create() eventually returns config_class(config_name, config_module).
        registry_config_class = None
        config_name = None
        config_module = None

        # If import_module succeeds, entry points to the registry module.
        try:
            config_module = import_module(entry)
        except Exception:
            pass
        else:
            # If config_module has a config submodule that defines a single
            # RegistryConfig subclass, use it automatically.
            if module_has_submodule(config_module, cls.lookup_module_name):
                mod_path = "%s.%s" % (entry, cls.lookup_module_name)
                mod = import_module(mod_path)
                # Check if there's exactly one RegistryConfig candidate
                registry_configs = [
                    (name, candidate)
                    for name, candidate in inspect.getmembers(mod, inspect.isclass)
                    if (issubclass(candidate, cls) and candidate is not cls)
                ]
                if len(registry_configs) == 1:
                    registry_config_class = registry_configs[0][1]

            # Use the default registry config class if we didn't find anything.
            if registry_config_class is None:
                registry_config_class = cls
                config_name = entry

        # If import_string succeeds, entry is a registry config class.
        if registry_config_class is None:
            try:
                registry_config_class = import_string(entry)
            except Exception:
                pass

        # If both import_module and import_string failed, it means that entry
        # doesn't have a valid value.
        if config_module is None and registry_config_class is None:
            # If the last component of entry starts with an uppercase letter,
            # then it was likely intended to be a registry config class; if not,
            # a config module. Provide a nice error message in both cases.
            mod_path, _, cls_name = entry.rpartition(".")
            if mod_path and cls_name[0].isupper():
                # This may raise ImportError, which is the best exception
                # possible if the module at mod_path cannot be imported.
                mod = import_module(mod_path)
                candidates = [
                    repr(name)
                    for name, candidate in inspect.getmembers(mod, inspect.isclass)
                    if issubclass(candidate, cls) and candidate is not cls
                ]
                msg = "Module '{}' does not contain a '{}' class.".format(
                    mod_path, cls_name
                )
                if candidates:
                    msg += " Choices are: {}.".format(", ".join(candidates))
                raise ImportError(msg)
            else:
                # Re-trigger the module import exception.
                import_module(entry)

        # Check for obvious errors. (This check prevents duck typing, but
        # it could be removed if it became a problem in practice.)
        if not issubclass(registry_config_class, RegistryConfig):
            raise ImproperlyConfigured(
                "'{}' isn't a subclass of {}.".format(entry, cls.__name__)
            )

        # Obtain config name here rather than in ConfigClass.__init__ to keep
        # all error checking for installed entries in one place.
        if config_name is None:
            try:
                config_name = registry_config_class.name
            except AttributeError:
                raise ImproperlyConfigured(
                    "'{}' must supply a name attribute.".format(entry)
                )

        # Ensure config_name points to a valid module.
        try:
            config_module = import_module(config_name)
        except ImportError:
            raise ImproperlyConfigured(
                "Cannot import '{}'. Check that '{}.{}.name' is correct.".format(
                    config_name,
                    registry_config_class.__module__,
                    registry_config_class.__qualname__,
                )
            )

        # Entry is a path to a registry config class.
        return registry_config_class(config_name, config_module)

    def import_managers(self) -> None:
        """Register registry manager if the config has the submodule required"""
        if module_has_submodule(self.module, MANAGER_MODULE_NAME):
            module_name = "%s.%s" % (self.name, MANAGER_MODULE_NAME)
            # Import will trigger __init_subclass__ of every subclass
            # found of BaseManager
            import_module(module_name)


class PluginConfig(RegistryConfig):
    """Class representing a Socon plugin and its configuration."""

    lookup_module_name = "plugins"


class ProjectSettings(LazySettings):
    _exclude_set_attr = ["_wrapped", "_project_config"]

    def __init__(self, project_config: ProjectConfig) -> None:
        super().__init__()
        self._project_config = project_config

    def _get_settings(self) -> str:
        return self._project_config.get_settings_module()


class ProjectConfig(RegistryConfig):
    """Class representing a Socon project and its configuration."""

    lookup_module_name = "projects"

    def __init__(self, project_name, project_module) -> None:
        super().__init__(project_name, project_module)
        self.settings = ProjectSettings(self)

        # Define settings module
        if not hasattr(self, "settings_module"):
            self.settings_module = "management.config"

    def get_settings_module(self) -> str:
        """Return the path to the configuration module"""
        return self.package + "." + self.settings_module

    def get_setting(
        self, setting: str, default: Optional[str] = None, skip: Optional[bool] = False
    ) -> str:
        """Return a project config setting

        :param name: Name of the setting.
        :param default: Default value to return in case the value
            does not exist and skip is True
        :param skip: If True, we return None. Else we raise a ValueError
        """
        msg = "{} setting does not exist in {} project".format(setting, self.label)
        return get_object_attr(self.settings, msg, setting, default, skip)
