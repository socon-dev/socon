from socon.core.manager import BaseManager


class FooManager(BaseManager):
    name = "foo"
    lookup_module = "test"


class BarManager(BaseManager):
    name = "foo"
    lookup_module = "test"
