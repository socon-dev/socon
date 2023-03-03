# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from functools import wraps
from typing import Any, Callable

from socon.conf import UserSettingsHolder, settings
from socon.core.registry import projects, registry


class override_settings:
    """
    A simple context manager (and decorator) class useful
    in tests which is necessary to change some
    setting in the safe way
    """

    def __init__(self, **kwargs: Any):
        self.options = kwargs

    def decorate_Callable(self, func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return inner

    def __call__(self, decorated: Callable) -> Callable:
        return self.decorate_Callable(decorated)

    def __enter__(self) -> None:
        # Keep this code at the beginning to leave the settings unchanged
        # in case it raises an exception because INSTALLED_PROJECTS is invalid.
        if "INSTALLED_PROJECTS" in self.options:
            try:
                skip_error = settings.SKIP_ERROR_ON_PROJECTS_IMPORT
                if "SKIP_ERROR_ON_PROJECTS_IMPORT" in self.options:
                    skip_error = self.options["SKIP_ERROR_ON_PROJECTS_IMPORT"]
                projects.set_installed_configs(
                    self.options["INSTALLED_PROJECTS"], skip_error=skip_error
                )
            except Exception:
                projects.unset_installed_configs()
                raise
        if "INSTALLED_PLUGINS" in self.options:
            try:
                registry.plugins.set_installed_configs(
                    self.options["INSTALLED_PLUGINS"]
                )
            except Exception:
                registry.plugins.unset_installed_configs()
                raise
        override = UserSettingsHolder(settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)
        self.wrapped = settings._wrapped
        settings._wrapped = override

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if "INSTALLED_PROJECTS" in self.options:
            projects.unset_installed_configs()
        if "INSTALLED_PLUGINS" in self.options:
            registry.plugins.unset_installed_configs()
        settings._wrapped = self.wrapped
        del self.wrapped
