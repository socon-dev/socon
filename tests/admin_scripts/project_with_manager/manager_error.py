from socon.core.manager import Hook


class SimpleHook(Hook):
    manager = "simple_manager"


raise ImportError("Test manager import error")
