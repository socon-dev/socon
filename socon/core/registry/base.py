# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

import os

from collections import Counter
from typing import List, Type

from socon.core.exceptions import ImproperlyConfigured, RegistryNotReady
from socon.core.registry.config import ProjectConfig, RegistryConfig


class BaseRegistry:
    """
    Base registry that stores different types of configuration.
    """

    def __init__(
        self,
        name: str,
        installed: set = (),
        config_class: Type[RegistryConfig] = RegistryConfig,
    ):
        # The name of the registry
        self.name = name

        # List of config instance installed.
        self.registry_configs = {}

        # Save the configs that we couldn't register
        self.unregistered_configs = {}

        # Whether the registry is populated.
        self.registry_ready = self.managers_ready = False

        # Save the registry main config class
        self.config_class = config_class

        # Lock the registry. If this is True, we can no longer
        # populate the registry.
        self.lock = False

        # Stack of registry configs. Used to store the current state in
        # set_available_configs and set_installed_configs.
        self.stored_configs = []

        # Populate projects and models, unless it's the master registry.
        if installed is not None:
            self.populate(installed)

    @property
    def single_registry_name(self) -> str:
        """Return single name of the registry"""
        if self.name.endswith("s"):
            return self.name[0 : len(self.name) - 1]
        return self.name

    def populate(
        self, installed: set = None, skip_error: bool = False, lock: bool = True
    ) -> None:
        """
        Load registry configurations and managers

        Import each configuration modules and then each managers
        """
        # In case the registry is lock. We return immediately
        if self.lock is True:
            return

        # If we call multiple times populate we don't want to import again
        # the configs manager. For this reason we save a local configs dict
        # in the function to import only the one in installed
        local_configs = {}

        # Lock the registry
        if lock is True:
            self.lock = lock

        # Initialize project configs and import project modules.
        for entry in installed:
            if isinstance(entry, self.config_class):
                registry_config = entry
            else:
                try:
                    registry_config = self.config_class.create(entry)
                except Exception as e:
                    if skip_error is False:
                        raise e
                    self.unregistered_configs[entry] = e
                    continue

            if registry_config.label in self.registry_configs:
                raise ImproperlyConfigured(
                    "{} labels aren't unique, duplicates: {}".format(
                        self.single_registry_name.title(), registry_config.label
                    )
                )
            self.registry_configs[registry_config.label] = registry_config
            local_configs[registry_config.label] = registry_config
            registry_config.registry = self

        # Check for duplicate config names.
        counts = Counter(
            registry_config.name for registry_config in self.registry_configs.values()
        )
        duplicates = [name for name, count in counts.most_common() if count > 1]
        if duplicates:
            name = self.single_registry_name.title()
            raise ImproperlyConfigured(
                "{} names aren't unique, "
                "duplicates: {}".format(name, ", ".join(duplicates))
            )

        # Registry is ready to use
        self.registry_ready = True

        # Phase 2: Register every managers. It is mandatory that they load
        # as a project might use it
        for config in local_configs.values():
            config.import_managers()

        # Managers of the registry are imported
        self.managers_ready = True

    def is_installed(self, name: str) -> bool:
        """
        Check whether a config with this name exists in the registry.
        ``name`` is the full name of the config.
        """
        self.check_registry_ready()
        return any(rc.name == name for rc in self.registry_configs.values())

    def set_installed_configs(self, installed: set, skip_error: bool = False) -> None:
        """Install configurations. Use only for test purpose."""
        self.stored_configs.append(self.registry_configs)
        self.registry_configs = {}
        self.registry_ready = self.lock = False
        self.populate(installed, skip_error)

    def unset_installed_configs(self) -> None:
        """Cancel a previous call to set_installed_projects()."""
        self.registry_configs = self.stored_configs.pop()
        self.registry_ready = self.lock = True

    def check_registry_ready(self) -> None:
        """Raise an exception if all configs haven't been imported yet."""
        if not self.registry_ready:
            from socon.conf import settings

            # If "not ready" is due to un-configured settings, accessing
            # a settings variable raises a more helpful ImproperlyConfigured
            # exception.
            settings.LOGGING
            name = self.name.title()
            raise RegistryNotReady(f"{name} aren't loaded yet.")

    def get_containing_registry_config(self, object_name: str) -> Type[RegistryConfig]:
        """
        Look for a registry config containing a given object.
        Return the config for the inner registry in case of nesting.
        Return None if the object isn't in any registered config.
        """
        self.check_registry_ready()
        candidates = []
        for config in self.registry_configs.values():
            if object_name.startswith(config.name):
                subpath = object_name[len(config.name) :]
                if subpath == "" or subpath[0] == ".":
                    candidates.append(config)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac.name))[0]

    def get_registry_configs(self) -> List[Type[RegistryConfig]]:
        """Return an iterable of registry configs."""
        self.check_registry_ready()
        return self.registry_configs.values()

    def get_registry_config(self, label: str) -> Type[RegistryConfig]:
        """
        Returns a config for the given label.
        Raise LookupError if no config exists with this label.
        """
        self.check_registry_ready()
        try:
            return self.registry_configs[label]
        except KeyError:
            message = "No installed {} with label '{}'.".format(
                self.single_registry_name, label
            )
            for config in self.get_registry_configs():
                if config.name == label:
                    message += " Did you mean '%s'?" % config.label
                    break
            raise LookupError(message)


class ProjectRegistry(BaseRegistry):
    """A registry that stores the configuration of installed projects"""

    def get_project_config_by_env(self) -> ProjectConfig:
        """
        Return a project configuration if the user has define the
        SOCON_ACTIVE_PROJECT environment variable
        """
        current_project = os.environ.get("SOCON_ACTIVE_PROJECT")
        if current_project:
            return self.get_registry_config(current_project)
        raise LookupError(
            "Cannot autodetect any project. You can find below the list "
            "of the available projects:\n"
            "{}".format([p.label for p in self.get_registry_configs()])
        )
