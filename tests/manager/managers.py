from socon.core.manager import BaseManager, Hook


class DefaultManager(BaseManager):
    name = "default"
    lookup_module = "lookup"


class HookOfDefaultManager(Hook, abstract=True):
    manager = "default"
