from argparse import ArgumentParser
from pathlib import Path
from typing import Union

from socon.core.management.base import CommandError, Config
from socon.core.management.templates import TemplateCommand
from socon.utils.terminal import terminal


class CreateProjectCommand(TemplateCommand):
    help: str = (
        "Creates a Socon project directory structure for the given project "
        "name in the projects directory."
    )
    missing_args_message: str = "You must provide a project name."
    template_prefix: str = "project"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("name", help="Name of the project.")
        parser.add_argument("--target", help=("Optional path to the project folder"))

    def handle(self, config: Config) -> Union[str, None]:
        project_name = config.getoption("name")
        target = config.getoption("target")
        super().handle(config, project_name, target)

    def check_target_directory(self, target: str, name: str) -> Path:
        if target is None:
            if Path.cwd().joinpath("manage.py").exists():
                top_dir = Path.cwd().joinpath("projects", name)
            else:
                raise CommandError("Can only create project at the root of a container")
            self._make_dirs(top_dir)
        else:
            top_dir = Path(target).expanduser().absolute()
            if top_dir.joinpath("manage.py").exists():
                top_dir = top_dir.joinpath("projects", name)
            elif top_dir.parent.name == "projects":
                if not top_dir.exists():
                    self.validate_name(top_dir.name, "directory")
                    terminal.write(
                        f"Project directory '{top_dir}' does not "
                        "exist, we will create it for you."
                    )
                    self._make_dirs(top_dir)
            elif top_dir.name == "projects":
                top_dir = top_dir.joinpath(name)
            else:
                raise CommandError(
                    "Target should be either the root of a container, "
                    "or a directory that exist or not in the projects container "
                    "directory."
                )
            if not top_dir.exists():
                self._make_dirs(top_dir)
        return top_dir
