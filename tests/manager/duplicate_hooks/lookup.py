from manager.managers import Hook


class FooHook(Hook):
    manager = "default"
    name = "foo"


class BarHook(Hook):
    manager = "default"
    name = "foo"
