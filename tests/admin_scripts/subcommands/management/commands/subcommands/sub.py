from socon.core.management.base import BaseCommand, Config


class SubOnecommand(BaseCommand):
    """Subcommand one"""

    name = "sub1"
    manager = "with_subs"

    def handle(self, config: Config) -> None:
        print("Subcommand of base-subcommand")


class SubTwocommand(BaseCommand):
    """Subcommand two"""

    name = "sub2"
    manager = "with_subs"
    keep_extras_args = True

    def handle(self, config: Config) -> None:
        print(config.extras_args)
