# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

from __future__ import annotations

import atexit
import logging
import os
import pkgutil
import shutil
import sys
import tempfile

from argparse import ArgumentParser, HelpFormatter, Namespace
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, Optional, Type, Union

import socon

from socon.core.exceptions import CommandNotFound, HookNotFound
from socon.core.manager import BaseManager, Hook
from socon.core.registry import projects, registry
from socon.core.registry.config import RegistryConfig
from socon.utils.func import get_object_attr
from socon.utils.terminal import TerminalWriter, terminal

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from socon.core.registry.config import ProjectConfig


class Config:
    """
    Base command configuration. Access to commands argument and
    extra arguments if requested.
    """

    def __init__(self, options: Namespace, extras_args: list = []) -> None:
        # Access to command line options as attribute
        self.options: Namespace = options

        # Keep extra argument if requested from the command. This is
        # useful if the user want to pass these args to another command
        self.extras_args: list = extras_args

        # Create a temporary directory at the start
        self.tmpdir: Path = Path(tempfile.mkdtemp())
        atexit.register(shutil.rmtree, self.tmpdir, ignore_errors=True)

        # TerminalWriter for the configuration
        self.terminal: TerminalWriter = terminal

    def getoption(
        self, name: str, default: Optional[str] = None, skip: Optional[bool] = True
    ) -> str:
        """Return command line option value.

        :param name: Name of the option.
        :param default: Default value to return in case the value
            does not exist and skip is True
        :param skip: If True, we return None. Else we raise a ValueError
        """
        msg = "No option named {}".format(name)
        return get_object_attr(self.options, msg, name, default, skip)


class CommandError(Exception):
    """
    Exception class indicating a problem while executing a management command.
    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.
    """

    def __init__(self, *args: Any, returncode: int = 1, **kwargs: Any) -> None:
        self.returncode = returncode
        super().__init__(*args, **kwargs)


class CommandParser(ArgumentParser):
    """
    Customized ArgumentParser class to improve some error messages and prevent
    SystemExit in several occasions, as SystemExit is unacceptable when a
    command is called programmatically.
    """

    def __init__(
        self,
        *,
        missing_args_message: Optional[Union[str, None]] = None,
        called_from_command_line: Optional[Union[bool, None]] = None,
        **kwargs: Any,
    ) -> None:
        self.missing_args_message = missing_args_message
        self.called_from_command_line = called_from_command_line
        super().__init__(**kwargs)

    def parse_args(self, args: list = None, namespace: Namespace = None) -> Namespace:
        # Catch missing argument for a better error message
        if self.missing_args_message and not (
            args or any(not arg.startswith("-") for arg in args)
        ):
            self.error(self.missing_args_message)
        return super().parse_args(args, namespace)

    def error(self, message) -> NoReturn:
        if self.called_from_command_line:
            super().error(message)
        else:
            raise CommandError("Error: %s" % message)


def handle_default_options(options: Namespace) -> None:
    """
    Include any default options that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.
    """
    if options.settings:
        os.environ["SOCON_SETTINGS_MODULE"] = options.settings
    if options.project:
        os.environ["SOCON_ACTIVE_PROJECT"] = options.project


class CustomHelpFormatter(HelpFormatter):
    """
    Customized formatter so that command-specific arguments appear in the
    --help output before arguments common to all commands.
    """

    show_last = {
        "--version",
        "--verbosity",
        "--traceback",
        "--settings",
    }

    def _reordered_actions(self, actions) -> list:
        return sorted(
            actions, key=lambda a: set(a.option_strings) & self.show_last != set()
        )

    def add_usage(self, usage, actions, *args, **kwargs) -> None:
        super().add_usage(usage, self._reordered_actions(actions), *args, **kwargs)

    def add_arguments(self, actions) -> None:
        super().add_arguments(self._reordered_actions(actions))


class CommandManager(BaseManager, name="commands"):
    lookup_module = "management.commands"

    def get_modules(self, config: Type[RegistryConfig]) -> list:
        """
        Iterate inside management.commands in order to register
        all Socon and users defined commands
        """
        command_dir = Path(config.path, self.lookup_module.replace(".", "/"))
        modules = [
            name
            for _, name, is_pkg in pkgutil.iter_modules([str(command_dir)])
            if not is_pkg and not name.startswith("_")
        ]

        # Base module name
        command_module = "{}.{}".format(config.name, self.lookup_module)

        # Loop over every module and get every class that are not abstract.
        # From these class we are going to get the commands that are
        # sublcalss of BaseCommand or ProjectCommand
        all_modules = []
        for cmd_module in modules:
            all_modules.append("{}.{}".format(command_module, cmd_module))
        return all_modules

    def get_hooks_config_holder_by_order(self) -> dict:
        """
        Return the hooks in specific order.
        Common hooks, then plugins and finally projects.
        """
        hooks = OrderedDict()
        for reg in registry.get_registries_by_importance_order():
            if reg in self.hooks:
                hooks[reg] = self.hooks[reg]
        return hooks

    def print_commands_usage(self, prog_name: str) -> None:
        """Nicely print commands usage"""
        # Show core, common and plugins commands. If the user wants to see
        # projects commands. They will need to specify the project
        terminal.line(
            "\n".join(
                [
                    "",
                    f"Type '{prog_name} help <subcommand>' for help on a specific "
                    "general (G) subcommand. If this command ",
                    "is a project (P) subcommand. Add --project <label> to the arguments.",
                    "",
                ]
            )
        )

        hooks_reg = self.get_hooks_config_holder_by_order()
        for reg, conf in hooks_reg.items():
            cmd_usage = "{} commands".format(reg.title())
            terminal.underline(cmd_usage)
            for config, hooks in conf.items():
                terminal.line(f"  [{config}]\n")
                for cmd_label, base_class in hooks.items():
                    if issubclass(base_class, ProjectCommand):
                        terminal.line(f"    {cmd_label} (P)")
                    else:
                        terminal.line(f"    {cmd_label} (G)")

                if config != list(conf)[-1]:
                    terminal.write("\n")

            if reg != list(hooks_reg)[-1]:
                terminal.write("\n")

    def search_command(self, name: str, project: str = None) -> Type[BaseCommand]:
        """Search a command and return its class"""
        current_project = os.environ.get("SOCON_ACTIVE_PROJECT")

        # If the user pass a project, it takes over the environment variable
        if project is not None:
            current_project = project

        project_config = None

        if current_project:
            try:
                project_config = projects.get_registry_config(current_project)
            except LookupError:
                raise CommandError(
                    f"You are looking for '{name}' command in  "
                    f"'{current_project}' project that is not installed. Please "
                    "check your INSTALLED_PROJECTS"
                )

        # Search for the right command hook implementation
        try:
            command = self.search_hook_impl(name, project_config)
        except HookNotFound as e:
            raise CommandNotFound(f"'{name}' command does not exist") from e

        return command


class BaseCommand(Hook, abstract=True):
    """
    The base class from which all management commands ultimately
    derive.

    Use this class if you want access to all of the mechanisms which
    parse the command-line arguments and work out what code to call in
    response; if you don't need to change any of that behavior,
    consider using one of the subclasses defined in this file.
    If you are interested in overriding/customizing various aspects of
    the command-parsing and -execution behavior, the normal flow works
    as follows:

    1. ``socon `` or ``manage.py`` loads the command class
        and calls its ``run_from_argv()`` method.

    2. The ``run_from_argv()`` method calls ``create_parser()`` to get
        an ``ArgumentParser`` for the arguments, parses them, performs
        any environment changes requested, and then calls the ``execute()``
        method, passing the parsed arguments.

    3. The ``execute()`` method attempts to carry out the command by
        calling the ``handle()`` method with the parsed arguments; any
        output produced by ``handle()`` will be printed to standard
        output.

    4. If ``handle()`` or ``execute()`` raised any exception (e.g.
        ``CommandError``), ``run_from_argv()`` will  instead print an error
        message to ``stderr``.

    Thus, the ``handle()`` method is typically the starting point for
    subclasses; many built-in commands and command types either place
    all of their logic in ``handle()``, or perform some additional
    parsing work in ``handle()`` and then delegate from it to more
    specialized methods as needed.
    """

    # Metadata about this command.
    help: str = ""

    # The manager of this hook
    manager = "commands"

    # The configuration that hold the command arguments and the property
    # to access them easily. The use can override this configuration
    # to implement it's own. This applies only if the new configuration
    # is a subclass of Config
    baseconfig: Type[Config] = Config

    # Keep extra args. Use parse_known_args instead of parse_args
    keep_extras_args: bool = False

    def __init__(self):
        # Will be define later in run_from_argv(...)
        self.config: Type[Config] = None

    def get_version(self) -> str:
        """
        Return the Socon version, which should be correct for all built-in
        Socon commands. User-supplied commands can override this method to
        return their own version.
        """
        return socon.get_version()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # We check if the subclass has declared it's own label. If it's not
        # the case, we are building it using the class name. We also remove
        # the Command part if present.
        if "name" not in cls.__dict__:
            name = cls.__name__
            if name.endswith("Command"):
                name = "".join(name.rsplit("Command", 1))
            cls.name = name.lower()

        super().__init_subclass__(**kwargs)

    def set_config(self, options: Namespace, extras_args: list = []) -> Type[Config]:
        """Set the command config"""
        self.config = self.baseconfig(options, extras_args)
        return self.config

    def create_parser(
        self, prog_name: str, subcommand: str, **kwargs: Any
    ) -> ArgumentParser:
        """
        Create and return the ``ArgumentParser`` which will be used to
        parse the arguments to this command.
        """
        parser = CommandParser(
            prog="%s %s" % (os.path.basename(prog_name), subcommand),
            description=self.help or None,
            formatter_class=CustomHelpFormatter,
            missing_args_message=getattr(self, "missing_args_message", None),
            called_from_command_line=getattr(self, "_called_from_command_line", None),
            **kwargs,
        )
        parser.add_argument("--version", action="version", version=self.get_version())
        parser.add_argument(
            "--settings",
            help=(
                "The Python path to a settings module, e.g. "
                '"myproject.settings.main". If this isn\'t provided, the '
                "SOCON_SETTINGS_MODULE environment variable will be used."
            ),
        )
        parser.add_argument(
            "--project",
            help=(
                "The project label of the command you want to start. "
                "This is mandatory only if you have a specific project command "
                "You can specify the SOCON_ACTIVE_PROJECT environment variable "
                "to avoid having to pass this argument all the time"
            ),
        )
        parser.add_argument(
            "--traceback", action="store_true", help="Raise on CommandError exceptions"
        )
        parser.add_argument(
            "-v",
            "--verbosity",
            default=1,
            type=int,
            choices=[0, 1, 2, 3],
            help="Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output",
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    def print_help(self, prog_name: str, subcommand: str) -> None:
        """
        Print the help message for this command, derived from
        ``self.usage()``.
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv: tuple) -> None:
        """
        Set up any environment changes requested (e.g., Python path
        and Socon settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        extras_args = []
        if self.keep_extras_args:
            options, extras_args = parser.parse_known_args(argv[2:])
        else:
            options = parser.parse_args(argv[2:])

        handle_default_options(options)

        # Create a config object that will store all the options
        config = self.set_config(options, extras_args)

        try:
            output = self.execute(config)
        except CommandError as e:
            if options.traceback:
                raise
            sys.stderr.write("%s: %s" % (e.__class__.__name__, e))
            sys.exit(e.returncode)
        else:
            if output:
                terminal.write(output)
            return output

    def execute(self, config: Config) -> None:
        """Execute the command"""
        return self.handle(config)

    def handle(self, config: Config) -> None:
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of BaseCommand must provide a handle() method"
        )


class ProjectCommand(BaseCommand, abstract=True):
    """
    The base class from which all project management commands ultimately derive.

    Use this class if you want access all of the mechanisms which
    parse the command-line arguments and work out what code to call in
    response. Subclassing this class will make all your commands project dependent.
    It means that you must pass the :option:`--project` to make it work.

    Subclassing the :class:`ProjectCommand` class requires that you implement the
    :meth:`~BaseCommand.handle` method.
    """

    projects = ["__all__"]

    def __init__(self) -> None:
        super().__init__()
        available_projects = [pc.label for pc in projects.get_registry_configs()]
        if "__all__" in self.projects:
            self.restricted_projects = available_projects
        else:
            self.restricted_projects = [
                label for label in available_projects if label in self.projects
            ]

    def execute(self, config: Config) -> None:
        """
        Execute the command. This function will first check if the
        project config is restricted to the use of this command
        """
        # Get the project config
        project_config = projects.get_project_config_by_env()
        if project_config.label not in self.restricted_projects:
            raise CommandError(
                "'{}' project does not have access to this command.\n"
                "List of authorized projects:\n{}".format(
                    project_config.label, "\n".join(self.restricted_projects)
                )
            )

        # Execute handler with config and project config
        return self.handle(config, project_config)

    def handle(self, config: Config, project_config: ProjectConfig):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of ProjectCommand must provide a handle() method"
        )
