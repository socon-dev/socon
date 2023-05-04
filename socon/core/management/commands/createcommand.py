import os

from argparse import ArgumentParser
from pathlib import Path
from typing import Union

from socon.conf import settings
from socon.core.management.base import CommandError, Config
from socon.core.management.templates import TemplateCommand


class CreateCommandCommand(TemplateCommand):
    help: str = (
        "Creates a Socon project or basecommand for a specific project"
        "(or in the common folder if no project is specified)"
    )
    missing_args_message: str = "You must provide a command name"
    template_prefix: str = "projectcommand"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("name", help="Name of the command")
        parser.add_argument(
            "--projectname",
            help=(
                "Name of the project where the command is to be created, default is None referring to the common folder"
            ),
            default=None,
        )
        parser.add_argument(
            "--type",
            help=("Type of command, defaults to project"),
            choices=["project", "base"],
            default="project",
        )
        parser.add_argument("--target", help=("Optional path to the project folder"))

    def handle(self, config: Config) -> Union[str, None]:
        command_name = config.getoption("name")
        project_name = config.getoption("projectname")
        command_type = config.getoption("type")
        target = config.getoption("target")

        self.template_prefix = command_type + "command"

        # handle target
        if target is None:
            top_dir = Path.cwd()
        else:
            top_dir = Path(target).expanduser().absolute()

        # handle project name
        if project_name is not None:
            if top_dir.joinpath(project_name, "setup.py").exists():
                top_dir = top_dir.joinpath(project_name, project_name)
            elif top_dir.joinpath(project_name, "plugins.py").exists():
                top_dir = top_dir.joinpath(project_name)
            elif top_dir.joinpath("manage.py").exists():
                # Common directory
                top_dir = top_dir.joinpath("projects", project_name)
            elif top_dir.name == "projects":
                top_dir = top_dir.joinpath(project_name)
            else:
                raise CommandError(
                    '--projectname "{:s}" could not be found in the target directory'.format(
                        project_name
                    )
                )

        super().handle(config, command_name, top_dir)

    def check_target_directory(self, target: str, name: str) -> Path:
        common_module_name = settings.get_settings_module_name()

        if common_module_name is None:
            # can occur in test environment
            for dir in os.listdir():
                settings_file = os.path.join(dir, "settings.py")
                if os.path.exists(settings_file):
                    common_module_name = os.path.dirname(settings_file)
                    break
        if (
            target.joinpath("setup.py").exists()
            and target.joinpath(target.name).exists()
        ):
            # inside specific plugin parent folder (thus no name needed)
            target = target.joinpath(target.name)
        elif target.joinpath("plugins.py").exists():
            # inside specific plugin folder (thus no name needed)
            pass
        elif target.joinpath("settings.py").exists():
            pass
        elif target.joinpath("manage.py").exists():
            target = target.joinpath(common_module_name)
        elif (
            target.parent.name == "projects" and target.joinpath("projects.py").exists()
        ):
            # inside specific projects folder (thus no name needed)
            pass
        else:
            raise CommandError(
                "Can only create a projectcommand at the root of the container/ project/ plugin"
            )
        return target
