# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from typing import Type

from socon.conf import settings
from socon.core.registry.base import BaseRegistry, ProjectRegistry
from socon.core.registry.config import PluginConfig, ProjectConfig, RegistryConfig

RegistryConfigType = Type[RegistryConfig]


class CoreRegistry:
    """Base class that store all socon registry"""

    # Define the projects registry. This will store all projects and will
    # be accessible by everyone. The registry will be populated if settings
    # are well configured.
    projects = ProjectRegistry(
        "projects",
        None,
        config_class=ProjectConfig,
    )

    # Same as projects but for plugins. Populated before the projects registry
    # to raise any error at start
    plugins = BaseRegistry("plugins", None, config_class=PluginConfig)

    # Create a common registry that will store core config (socon.core) and
    # later the container config if it exists. We initialize first the
    # registry with socon.core so we can register main managers of Socon
    common = BaseRegistry("common", None)

    def __init__(self) -> None:
        # Populate the common registry but do not lock it. We will lock it
        # when we will registry user common configuration
        self.common.populate(installed=("socon.core",), lock=False)

        # Save all the registries by importance order. Projects
        # being the most important.
        self.registries: list[Type[BaseRegistry]] = [
            self.common,
            self.plugins,
            self.projects,
        ]

    def get_user_common_config(self) -> RegistryConfigType:
        """Get the main user common config"""
        settings_module = settings.get_settings_module_name()
        if settings_module:
            return self.common.get_registry_config(settings_module)

    def get_socon_common_config(self) -> RegistryConfigType:
        """Get Socon core config"""
        return self.common.get_registry_config("core")

    def get_user_configs(self) -> list[RegistryConfigType]:
        """
        Get all projects and plugins configs that the user registered
        in the global settings
        """
        user_configs = []
        for registry in (self.projects, self.plugins):
            user_configs.extend(registry.get_registry_configs())
        return user_configs

    def get_registries_by_importance_order(self) -> list:
        """
        Return each registries by importance order. Last being the most important
        """
        return [self.common.name, self.plugins.name, self.projects.name]

    def get_containing_registry_config(self, object_name: str) -> RegistryConfigType:
        """
        Look for a registry config containing a given object.
        Return the config for the inner registry in case of nesting.
        Return None if the object isn't in any registered config. This
        check in every socon registry
        """
        candidates = []
        for registry in self.registries:
            if registry.registry_ready is False:
                continue
            config = registry.get_containing_registry_config(object_name)
            if config is not None:
                candidates.append(config)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac.name))[0]


registry = CoreRegistry()
