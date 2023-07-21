# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

from __future__ import annotations

import os
import sys

from difflib import get_close_matches
from typing import TYPE_CHECKING, Type

import socon

from socon.conf import settings
from socon.core.exceptions import CommandNotFound, ImproperlyConfigured
from socon.core.management.base import (
    CommandError,
    CommandParser,
    handle_default_options,
)
from socon.core.manager import managers
from socon.core.registry import projects
from socon.utils.func import set_env
from socon.utils.terminal import terminal

if TYPE_CHECKING:
    from socon.core.management.base import BaseCommand, CommandManager


def get_commands(manager: str = "commands") -> CommandManager:
    """
    Return a CommandManager instance that hold all the commands. The
    registry will look for every modules in management.commands in each registry
    config. This mean the core registry config, the common config of the user
    and every projects and plugins. Core commands are always included.
    """
    command_manager = managers.get_manager(manager)
    return command_manager.find_all()


class ManagementUtility:
    """
    Encapsulate the logic of the socon and manage.py utilities.
    """

    def __init__(self, argv: list = None) -> None:
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        if self.prog_name == "__main__.py":
            self.prog_name = "python -m socon"
        self.settings_exception = None

    def main_help_text(self) -> None:
        """Print script's main help text."""
        commands = get_commands()
        usage = commands.get_commands_usage(self.prog_name)
        terminal.write(f"{usage}\n")

        # Output an extra note if settings are not properly configured
        if self.settings_exception is not None:
            terminal.write("\n")
            terminal.sep("-", "Settings error")
            terminal.line(
                "\n"
                "Note that only Socon core commands are listed "
                "as settings are not properly configured (error: %s)."
                % self.settings_exception
            )

        if projects.registry_ready and projects.unregistered_configs:
            # Show all unregistered projects if any
            terminal.write("\n")
            terminal.sep("-", "Project loading error")
            terminal.line(
                "\n"
                "Some of your projects didn't load correctly. If you "
                "want more informations about the errors, use the 'verify' "
                "command. List of projects:"
            )
            for unregistered in projects.unregistered_configs:
                terminal.line(unregistered)

        terminal.write("\n")

    def fetch_command(self, subcommand: str) -> Type[BaseCommand]:
        """
        Try to fetch the given subcommand, printing a message with the
        appropriate command called from the command line (usually
        "socon" or "manage.py") if it can't be found.
        """
        # Get commands outside of try block to prevent swallowing exceptions
        commands = get_commands()
        try:
            command = commands.search_command(subcommand)
        except CommandNotFound:
            if os.environ.get("SOCON_SETTINGS_MODULE"):
                # If `subcommand` is missing due to misconfigured settings, the
                # following line will retrigger an ImproperlyConfigured exception
                # (get_commands() swallows the original one) so the user is
                # informed about it.
                settings.INSTALLED_PROJECTS
            elif not settings.configured:
                sys.stderr.write("No Socon settings specified.\n")
            possible_matches = get_close_matches(subcommand, commands.get_hooks_name())
            sys.stderr.write("Unknown command: '{}'".format(subcommand))
            if possible_matches:
                if subcommand != possible_matches[0]:
                    sys.stderr.write(". Did you mean %s?" % possible_matches[0])
                else:
                    # If the command is equal to subcommand it means that the
                    # command might exist for a project but it's not reachable
                    # The idea is to show which projects is associated with
                    # this command
                    holders = commands.get_hook_config_holders(subcommand)
                    sys.stderr.write(
                        ". You might have missed to specify the project. "
                        "You must either define the environment variable "
                        "SOCON_ACTIVE_PROJECT or add the --project argument to the command.\n"
                        "You can find below the list of the projects available: "
                    )
                    for holder in holders:
                        sys.stderr.write(holder)

            sys.stderr.write("\nType '%s help' for usage.\n" % self.prog_name)
            sys.exit(1)

        return command()

    def execute(self) -> None:
        """
        Given the command-line arguments, figure out which subcommand is being
        run, create a parser appropriate to that command, and run it.
        """
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = "help"  # Display help if no arguments were given.

        # Preprocess options to extract --settings
        # These options could affect the commands that are available, so they
        # must be processed early.
        parser = CommandParser(
            usage="%(prog)s subcommand [options] [args]",
            add_help=False,
            allow_abbrev=False,
        )
        parser.add_argument("--settings")
        parser.add_argument("--project")
        parser.add_argument("args", nargs="*")  # catch-all
        try:
            options, _ = parser.parse_known_args(self.argv[2:])
            handle_default_options(options)
        except CommandError:
            pass  # Ignore any option errors at this point.

        # As settings is the entry point of the entire project, we
        # try to load it and check if there is no error associated to it.
        # If it's the case, we save the error to diplay it.
        try:
            settings.INSTALLED_PROJECTS
        except ImproperlyConfigured as exc:
            self.settings_exception = exc
        except ImportError as exc:
            self.settings_exception = exc

        # Setup = Populate project / plugins registry and configure logging
        if settings.configured:
            socon.setup()

        if subcommand == "help":
            if not options.args:
                self.main_help_text()
            else:
                self.fetch_command(options.args[0]).print_help(
                    self.prog_name, options.args[0]
                )
        elif subcommand == "version" or self.argv[1:] == ["--version"]:
            sys.stdout.write(socon.get_version() + "\n")
        elif self.argv[1:] in (["--help"], ["-h"]):
            self.main_help_text()
        else:
            self.fetch_command(subcommand).run_from_argv(self.argv)


def call_command(name: str, *args):
    """Call the given command, with the given args/options. Example:

    call_command('createcontainer', 'test_container', '--target', 'directory')

    :param name: Name of the command
    :param *args: Arguments for the command
    :return: Command output
    """
    command_manager = get_commands()

    # Check if the user passed a project in order to get the right command
    parse_args = []
    project = ""
    for i, arg in enumerate(args):
        parse_args.append(str(arg))
        if arg == "--project":
            try:
                project = args[i + 1]
            except IndexError:
                raise CommandError("Project was passed but not defined")

    # Search for the command
    command = command_manager.search_command(name, project)()

    # Create the parser and save the args
    parser = command.create_parser("", name)

    # Parser the args
    extras_args = []
    if command.keep_extras_args:
        cmd_args, extras_args = parser.parse_known_args(parse_args)
    else:
        cmd_args = parser.parse_args(parse_args)

    # Create the conmand config object
    config = command.set_config(cmd_args, extras_args)

    # We change the active project for the command using a context manager. This is
    # important as the execute command for a ProjectCommand, will look for
    # the SOCON_ACTIVE_PROJECT environment to set the project_config of that command.
    project = project if project else os.environ.get("SOCON_ACTIVE_PROJECT", "")
    with set_env(SOCON_ACTIVE_PROJECT=project):
        return command.execute(config)


def execute_from_command_line(argv: list = None) -> None:
    """Run a ManagementUtility."""
    utility = ManagementUtility(argv)
    utility.execute()
