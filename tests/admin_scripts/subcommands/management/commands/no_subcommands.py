from socon.core.management.subcommand import Subcommand


class NoSubcommand(Subcommand):
    name = "no-subs"
    subcommand_manager = "without_subs"
