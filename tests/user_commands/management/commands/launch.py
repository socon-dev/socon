from socon.core.management.base import BaseCommand, CommandError, Config
from socon.utils.terminal import TerminalWriter


class LaunchCommand(BaseCommand):
    name = "launch"
    help = "Launch NASA's spaceship"

    def add_arguments(self, parser):
        parser.add_argument("integer", nargs="?", type=int, default=0)
        parser.add_argument("-s", "--spaceship")
        parser.add_argument("-x", "--example")

    def handle(self, config: Config):
        terminal = TerminalWriter()
        if config.getoption("spaceship"):
            terminal.line("Launching {}".format(config.options.spaceship))
        if config.getoption("example") == "raise":
            raise CommandError(returncode=3)
        integer = config.getoption("integer")
        if integer > 0:
            terminal.line("You passed {} as a positional argument.".format(integer))


class LaunchExtrasArgs(BaseCommand):
    name = "launch_extras"
    keep_extras_args = True

    def handle(self, config: Config):
        terminal = TerminalWriter()
        terminal.line("Extras args = {}".format(config.extras_args))
