from socon.core.manager import BaseManager, Hook


class Registry(BaseManager):
    name = "test_manager"
    lookup_module = "test_module"


class Manager(Hook):
    manager = "test_manager"
