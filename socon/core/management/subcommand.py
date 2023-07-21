import sys

from typing import Any, List, Optional, Type

from socon.core.exceptions import CommandNotFound, ImproperlyConfigured
from socon.core.management import get_commands
from socon.core.management.base import (
    BaseCommand,
    CommandManager,
    Config,
    handle_default_options,
)
from socon.utils.terminal import terminal


class SubcommandManager(CommandManager):
    name = "subcommands"
    lookup_module = "management.commands.subcommands"

    def get_usage_message(self, prog_name: str) -> List[str]:
        return ["List of available subcommands:"]


class Subcommand(BaseCommand, abstract=True):
    """
    Base class for every commands carry subcommands.
    A subcommand can by of any type (ProjectCommand or BaseCommand). Each
    subcommand must inherit from this class and set the `subcommand_manager` attribute
    """

    # The name of the manager that holds the subcommands
    subcommand_manager: Optional[str] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # If the base class has not been linked to a registry, we raise
        # an error as we won't be able to register the subclass
        if cls.subcommand_manager is None:
            raise ImproperlyConfigured(
                "{} class must link a subcommand manager".format(cls.__name__)
            )

    def get_subcommands(self) -> Type[CommandManager]:
        """Get the list of subcommands for the specific project"""
        return get_commands(self.subcommand_manager)

    def get_subcommand(self, subcommand: str, argv: list) -> Type[BaseCommand]:
        subcommands = self.get_subcommands()
        try:
            command = subcommands.search_command(subcommand)
            return command()
        except CommandNotFound:
            sys.stderr.write("Error: Unknown subcommand '{}'\n".format(subcommand))
            self.print_help(argv[0], f"{argv[1]} SUBCOMMAND")
            sys.exit(1)

    def print_help(self, prog_name, subcommand):
        commands = self.get_subcommands()
        usage = commands.get_commands_usage(prog_name, show_registry=False)
        super().print_help(prog_name, subcommand)
        terminal.write("{}\n\n".format(usage))

    def parse_args(self, argv: tuple) -> Config:
        """Parse command line arguments for subcommands"""
        self.argv = argv
        subcommand = None
        if len(argv) > 2 and not argv[2].startswith("-"):
            subcommand = argv[2]
            command = self.get_subcommand(subcommand, argv)
            parser = command.create_parser(argv[0], "{} {}".format(argv[1], subcommand))
            parse_argv = argv[3:]
        else:
            parser = self.create_parser(argv[0], argv[1])
            parse_argv = argv[2:]
            command = self

        if subcommand is None:
            self.print_help(argv[0], f"{argv[1]} SUBCOMMAND")
            sys.exit(0)

        extras_args = []
        if command.keep_extras_args:
            options, extras_args = parser.parse_known_args(parse_argv)
        else:
            options = parser.parse_args(parse_argv)

        handle_default_options(options)

        # Set the subcommand in the options here as we don't want to add
        # the subcommand as a positional arg. This is to avoid wrong help
        # message when we run the subcommand.
        setattr(options, "subcommand", subcommand)

        # Create a config object that will store all the options
        return command.baseconfig(options, extras_args)

    def handle(self, config: Config):
        """Execute the subcommand"""
        subcommand = config.getoption("subcommand")
        command = self.get_subcommand(subcommand, self.argv)
        return command.execute(config)
