from socon.core.management.subcommand import Subcommand


class MainSubcommand(Subcommand):
    name = "base-subcommand"
    subcommand_manager = "with_subs"
