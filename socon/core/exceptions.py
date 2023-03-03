"""
Global Socon exception and warning classes.
"""


class ImproperlyConfigured(Exception):
    """Socon is somehow improperly configured"""


class RegistryNotReady(Exception):
    """Raised when the registry is not ready"""


class CommandNotFound(Exception):
    """The command cannot be found"""


class ManagerNotHooked(Exception):
    """The manager does not contain any hook implementation"""


class ManagerNotFound(Exception):
    """Manager is not found"""


class HookNotFound(Exception):
    """Cannot find the hook in the manager"""
