from socon.core.management.subcommand import SubcommandManager


class SubManagerWithSubcommands(SubcommandManager):
    name = "with_subs"


class SubManagerWithoutSubcommands(SubcommandManager):
    name = "without_subs"
