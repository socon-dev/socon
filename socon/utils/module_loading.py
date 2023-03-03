# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) Django Software Foundation and individual contributors

from importlib import import_module
from importlib.util import find_spec as importlib_find
from types import ModuleType
from typing import Any


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


def module_has_submodule(package: ModuleType, module_name: str) -> bool:
    """See if 'module' is in 'package'."""
    try:
        package_name = package.__name__
        package_path = package.__path__
    except AttributeError:
        # package isn't a package.
        return False

    full_module_name = package_name + "." + module_name
    try:
        return importlib_find(full_module_name, package_path) is not None
    except ModuleNotFoundError:
        return False
