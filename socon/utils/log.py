# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

import logging
import logging.config

from socon.utils.module_loading import import_string

DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}


def configure_logging(logging_config: str, logging_settings: str) -> None:
    """Configure logging on load"""
    if logging_config:
        # First find the logging configuration function ...
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        # ... then invoke it with the logging settings
        if logging_settings:
            logging_config_func(logging_settings)
