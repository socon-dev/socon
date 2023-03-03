from manager.managers import HookOfDefaultManager


class AbstractHook(HookOfDefaultManager, abstract=True):
    name = "abstract"


class WillBeRegistered(AbstractHook):
    name = "will_be_register"
