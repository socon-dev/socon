"""
Default Socon settings. Override these with settings in the module pointed to
by the SOCON_SETTINGS_MODULE environment variable.
"""

# ---------------------------------------------------------------------------- #
#                                     CORE                                     #
# ---------------------------------------------------------------------------- #

# List of strings representing installed plugins
INSTALLED_PLUGINS = []

# List of strings representing users projects
INSTALLED_PROJECTS = []

# By default if there is an issue when importing a config we raise it.
# We can skip the raise error by setting this config to True. Default
# is True as we don't want project to break other project on import
SKIP_ERROR_ON_PROJECTS_IMPORT = True

# ---------------------------------------------------------------------------- #
#                                    LOGGING                                   #
# ---------------------------------------------------------------------------- #

# The callable to use to configure logging
LOGGING_CONFIG = "logging.config.dictConfig"

# Custom logging configuration.
LOGGING = {}
