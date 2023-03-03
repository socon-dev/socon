# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from typing import Any, Optional


def get_object_attr(
    obj: object,
    msg: str,
    name: str,
    default: Optional[str] = None,
    skip: Optional[bool] = True,
) -> Any:
    """
    Return a value from any object attribute. This function allow you to
    pass a default value if not found or raise a ValueError
    """
    try:
        val = getattr(obj, name)
        if val is None:
            raise AttributeError
        return val
    except AttributeError as e:
        if skip:
            return default
        raise ValueError(msg) from e
