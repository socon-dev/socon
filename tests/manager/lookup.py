from manager.managers import HookOfDefaultManager


class FooManager(HookOfDefaultManager):
    name = "foo"

    def execute(self):
        return "Execute from manager"


class BarManager(HookOfDefaultManager):
    name = "bar"
