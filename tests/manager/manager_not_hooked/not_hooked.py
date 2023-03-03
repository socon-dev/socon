from socon.core.manager import Hook


class TestHook(Hook):
    manager = "not_hooked_manager"
