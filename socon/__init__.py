# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from socon.utils.version import get_version

VERSION = (0, 2, 0, "rc", 1)

__version__ = get_version(VERSION)


def setup() -> None:
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the config registries.
    """
    from socon.conf import settings
    from socon.core.registry import projects, registry
    from socon.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    # Populate the registry. First the plugins so we can catch errors before
    # loading the projects.
    registry.plugins.populate(settings.INSTALLED_PLUGINS)

    # Populate the projects. If there is an error while importing all
    # the projects, skip it so we can handle it later.
    projects.populate(
        settings.INSTALLED_PROJECTS, skip_error=settings.SKIP_ERROR_ON_PROJECTS_IMPORT
    )

    # Create the container config. This config act as the common ground for
    # all user projects managers and commands. We create this config based on
    # the container name.
    container_name = settings.get_settings_module_name()
    if container_name is not None:
        registry.common.populate([container_name], skip_error=True)
