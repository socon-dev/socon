import os

from argparse import ArgumentParser
from pathlib import Path
from typing import Union

from socon.conf import settings
from socon.core.management.base import CommandError, Config
from socon.core.management.templates import TemplateCommand


class CreateCommandCommand(TemplateCommand):
    help: str = (
        "Creates a Socon projectcommand or basecommand. "
        "If called from the root it will create a common command. "
        "If called from the root/projects folder --projectname can be defined to create a command inside a project folder. "
        "If called from a plugin folder or inside a project folder --projectname is not needed."
    )
    missing_args_message: str = "You must provide a command name"
    template_prefix: str = "projectcommand"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("name", help="Name of the command")
        parser.add_argument(
            "--projectname",
            help=(
                'Name of the project where the command is to be created, default is "None" referring to the common folder'
            ),
            default="None",
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
            target = Path(os.path.abspath(os.getcwd()))
        else:
            # resolve ~, ..\ etc.
            target = Path(os.path.abspath(os.path.expanduser(target)))

        # evaluate working directory and handle project name
        if target.joinpath("setup.py").exists():
            # Plugin parent folder
            if project_name != "None":
                target = target.joinpath(project_name)
            else:
                target = target.joinpath(target.name)

            if not target.exists():
                raise CommandError(
                    "Looking for non-existing plugin folder {:s}".format(
                        project_name if project_name != "None" else target.name
                    )
                )
        elif target.joinpath("plugins.py").exists():
            # Plugin folder
            if project_name != "None" and project_name != target.name:
                raise CommandError(
                    '--projectname "{:s}" given, but command called in pluginfolder {:s}'.format(
                        project_name, target.name
                    )
                )
        elif target.joinpath("manage.py").exists():
            # Root directory
            if project_name != "None":
                # select project folder
                target = target.joinpath("projects", project_name)

                if not target.exists():
                    raise CommandError(
                        'Project "{:s}" could not be found'.format(project_name)
                    )
            else:
                # select common folder
                common_module_name = settings.get_settings_module_name()
                if common_module_name is None:
                    # can occur in test environment
                    # (could also assume common folder to equal (target.name))
                    for dir in os.listdir(target):
                        settings_file = os.path.join(dir, "settings.py")
                        if os.path.exists(settings_file):
                            common_module_name = os.path.dirname(settings_file)
                            break
                target = target.joinpath(common_module_name)
        elif target.name == "projects":
            # projects folder
            if project_name != "None":
                target = target.joinpath(project_name)

                if not target.exists():
                    raise CommandError(
                        'Project "{:s}" could not be found'.format(project_name)
                    )
            else:
                raise CommandError(
                    "--projectname should be specified when creating a command from the projects folder"
                )
        elif target.joinpath("projects.py").exists():
            if project_name != "None" and target.name != project_name:
                raise CommandError(
                    '--projectname "{:s}" given, but command called inside the project "{:s}"'.format(
                        project_name, target.name
                    )
                )
        else:
            raise CommandError(
                "Can only create a projectcommand at the root of the container/ project/ plugin, or inside the plugin/ project folder"
            )

        super().handle(config, command_name, target)

    def check_target_directory(self, target: str, name: str) -> Path:
        if not Path(target).exists():
            raise CommandError("Directory {:s} does not exist".format(target))
        return target
