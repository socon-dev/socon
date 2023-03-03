import sys

from argparse import ArgumentParser
from traceback import TracebackException

from socon.conf import settings
from socon.core.management.base import BaseCommand, CommandError, Config
from socon.core.manager import BaseManager
from socon.core.registry import projects, registry


class CheckCommand(BaseCommand):
    help: str = "Check the integrity of any installed projects and their managers"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--show_all", help="Show all projects error at once", action="store_true"
        )

    def handle(self, config: Config) -> None:
        # Check that the settings are configured.
        terminal = config.terminal
        if not settings.configured:
            raise CommandError(
                "Settings are not configured. You must either define the environment "
                "variable SOCON_SETTINGS_MODULE or call settings.configure(). \n"
                "You should call this command with manage.py that load the configuration "
                "for you.\n"
            )

        # First check is to see if there is any unloaded configuration
        # This is only available if settings.SKIP_ERROR_ON_PROJECTS_IMPORT is True
        if settings.SKIP_ERROR_ON_PROJECTS_IMPORT is True:
            terminal.sep("-", "Projects check")
            unreg_length = len(projects.unregistered_configs)
            if unreg_length == 0:
                terminal.line("Nothing to report. All projects loaded successfully.\n")
            else:
                terminal.write("\n")
            for unregistered, e in projects.unregistered_configs.items():
                terminal.underline(unregistered)
                self.show_traceback(config, e)

        # Get all configs that we want to check
        configs = [registry.get_user_common_config()]
        configs.extend(registry.get_user_configs())

        # Check that we can import all managers for each project.
        raised_issue = 0
        terminal.sep("-", "Managers check")
        for manager in BaseManager.get_managers():
            for registry_config in configs:
                try:
                    manager.find_hooks_impl(registry_config)
                except Exception as e:
                    raised_issue += 1
                    terminal.write("\n")
                    terminal.underline(registry_config.name)
                    self.show_traceback(config, e)

        if raised_issue == 0:
            terminal.line("Nothing to report. All managers loaded successfully.\n")

        # Exit 1 if there is any issue found
        if len(projects.unregistered_configs) != 0 or raised_issue != 0:
            sys.exit(1)

    def show_traceback(self, config: Config, e: Exception):
        """Show or raise exception"""
        if config.options.show_all is True:
            config.terminal.line("".join(TracebackException.from_exception(e).format()))
        else:
            raise e
