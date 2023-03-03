# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

"""
Settings and configuration for Socon.
Read values from the module specified by the SOCON_SETTINGS_MODULE environment
variable, and then from socon.conf.global_settings; see the global_settings.py
for a list of all possible variables.
"""
from __future__ import annotations

import copy
import importlib
import inspect
import os

from typing import Any, Type, Union

from socon.core.exceptions import ImproperlyConfigured

ENVIRONMENT_VARIABLE = "SOCON_SETTINGS_MODULE"

empty = object()


def new_method_proxy(func) -> Any:
    """
    Proxy for class method. This will ensure that on call of the
    method, we call the _setup method to configure the LazySetting
    """

    def inner(self, *args):
        if self._wrapped is empty:
            self._setup()
        return func(self._wrapped, *args)

    return inner


class LazySettings:
    """
    A lazy proxy for either global Socon settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    Socon uses the settings module return by the ``_get_settings`` method.
    """

    # Avoid infinite recursion when tracing __init__
    _wrapped = None

    # Avoid infinite __setattr__
    _exclude_set_attr: list = ["_wrapped"]

    def __init__(self) -> None:
        # Note: if a subclass overrides __init__(), it will likely need to
        # override __copy__() and __deepcopy__() as well.
        self._wrapped = empty

    def _setup(self, name: str = None) -> None:
        """
        Load the settings module return by the _get_settings method. This
        is used the first time settings are needed, if the user hasn't
        configured settings manually.
        """
        settings_module = self._get_settings()
        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            message = self._get_improperly_configure_msg(desc)
            raise ImproperlyConfigured(message)

        wrapper = Settings(settings_module)
        self._initialize_wrapper(wrapper)

    def __repr__(self) -> str:
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return "<LazySettings [Unevaluated]>"
        return '<LazySettings "%(settings_module)s">' % {
            "settings_module": self._wrapped.SETTINGS_MODULE,
        }

    def _get_settings(self) -> str:
        """
        Get the settings when _setup is called for the first
        time and _settings_list is empty.
        """
        raise NotImplementedError(
            "Subclass of LazySettings must define _get_settings method. "
            "This function need to return the settings module."
        )

    def _initialize_wrapper(self, wrapper: Type[Settings]) -> None:
        """
        Load the settings. Register only UPPERCASE settings unless
        redefined differently.
        """
        wrapper._load_settings()
        self._wrapped = wrapper

    def _get_improperly_configure_msg(self, desc: str) -> str:
        return f"Requested {desc}, but settings are not configured."

    def __getattr__(self, name: str) -> Any:
        """Return the value of a setting and cache it in self.__dict__."""
        if (_wrapped := self._wrapped) is empty:
            self._setup(name)
            _wrapped = self._wrapped
        val = getattr(_wrapped, name)

        self.__dict__[name] = val
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        (@override_settings does this) or clear single values when set.
        """
        if name in self._exclude_set_attr:
            if name == "_wrapped":
                self.__dict__.clear()
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__[name] = value
        else:
            self.__dict__.pop(name, None)
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name: str) -> None:
        """Delete a setting and clear it from cache if needed."""
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)
        self.__dict__.pop(name, None)

    def configure(self, default_settings: Any, **options: Any) -> None:
        """
        Called to manually configure the settings. The 'default_settings'
        parameter sets where to retrieve any unspecified values from (its
        argument must support attribute access (__getattr__)).
        """
        if self._wrapped is not empty:
            raise RuntimeError("Settings already configured.")
        holder = UserSettingsHolder(default_settings)
        for name, value in options.items():
            if not name.isupper():
                raise TypeError("Setting %r must be uppercase." % name)
            setattr(holder, name, value)
        self._wrapped = holder

    @property
    def configured(self):
        """Return True if the settings have already been configured."""
        return self._wrapped is not empty

    def __copy__(self) -> Union[Type[Settings], UserSettingsHolder]:
        if self._wrapped is empty:
            return type(self)()
        else:
            # If initialized, return a copy of the wrapped object.
            return copy.copy(self._wrapped)

    def __deepcopy__(self, memo: dict) -> Union[Type[Settings], UserSettingsHolder]:
        if self._wrapped is empty:
            # We have to use type(self), not self.__class__, because the
            # latter is proxied.
            result = type(self)()
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    # Introspection support
    __dir__ = new_method_proxy(dir)


class CoreSettings(LazySettings):
    """
    Core settings for Socon. Will load global_settings + the
    settings configured by the user.
    """

    def _get_improperly_configure_msg(self, desc: str) -> str:
        return (
            "Requested {}, but settings are not configured. "
            "You must either define the environment variable {} "
            "or call settings.configure() before accessing settings.".format(
                desc, ENVIRONMENT_VARIABLE
            )
        )

    def _get_settings(self) -> str:
        return os.environ.get(ENVIRONMENT_VARIABLE)

    def _initialize_wrapper(self, wrapper: Type[Settings]):
        # Insert global settings before the other settings. This way
        # it's the global settings that are override first
        wrapper._add_settings("socon.conf.global_settings", is_explicit=False)
        super()._initialize_wrapper(wrapper)

    def get_settings_module_name(self) -> Union[str, None]:
        """Get the module name that hold the settings and return it if exist"""
        if self.configured:
            settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
            if not settings_module:
                return None
            return settings_module.split(".")[0]


class Settings:
    """Base class that will hold all settings attribute"""

    def __init__(self, settings_module: Any) -> None:
        self.configured = False
        self._settings_module = settings_module
        self._explicit_settings = set()

    def _add_settings(self, settings_file: str, is_explicit: bool = True) -> None:
        """Set attribute settings from the settings_file"""
        mod = importlib.import_module(settings_file)
        for setting in (s for s in dir(mod) if not s.startswith("_")):
            setting_value = getattr(mod, setting)
            if setting.isupper() and not inspect.ismodule(setting_value):
                setattr(self, setting, setting_value)
                if is_explicit:
                    self._explicit_settings.add(setting)

    def _load_settings(self) -> None:
        """Load the settings"""
        self._add_settings(self._settings_module)

    def is_overridden(self, setting: str) -> bool:
        """Check if any settings attribute have been overridden"""
        return setting in self._explicit_settings

    @property
    def SETTINGS_MODULE(self) -> str:
        return self._settings_module

    def __repr__(self) -> str:
        return '<%(cls)s "%(settings_module)s">' % {
            "cls": self.__class__.__name__,
            "settings_module": self.SETTINGS_MODULE,
        }


class UserSettingsHolder:
    """Holder for user configured settings."""

    # SETTINGS_MODULE doesn't make much sense in the manually configured
    # (standalone) case.
    SETTINGS_MODULE = None

    def __init__(self, default_settings: Any) -> None:
        """
        Requests for configuration variables not in this class are satisfied
        from the module specified in default_settings (if possible).
        """
        self.__dict__["_deleted"] = set()
        self.default_settings = default_settings

    def __getattr__(self, name: str) -> None:
        if not name.isupper() or name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._deleted.discard(name)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        self._deleted.add(name)
        if hasattr(self, name):
            super().__delattr__(name)

    def __dir__(self) -> list:
        return sorted(
            s
            for s in [*self.__dict__, *dir(self.default_settings)]
            if s not in self._deleted
        )

    def is_overridden(self, setting: str) -> bool:
        """Check if a setting has been overridden"""
        deleted = setting in self._deleted
        set_locally = setting in self.__dict__
        set_on_default = getattr(
            self.default_settings, "is_overridden", lambda s: False
        )(setting)
        return deleted or set_locally or set_on_default

    def __repr__(self) -> None:
        return "<%(cls)s>" % {
            "cls": self.__class__.__name__,
        }


settings = CoreSettings()
