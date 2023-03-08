# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-BSD3-Clause-Django
# Copyright (c) 2023, Stephane Capponi and Others

import os
import shutil

from importlib import import_module
from pathlib import Path
from typing import Optional

import socon

from socon.core.management.base import BaseCommand, CommandError, Config
from socon.utils.reshape import FileReshape
from socon.utils.terminal import terminal
from socon.utils.version import get_docs_version


class TemplateCommand(BaseCommand, abstract=True):
    """
    Copy a template layout from container, plugins or projects into the
    specified directory.

    :param name: The name of the container, project or plugin.
    """

    # Rewrite the following suffixes when determining the target filename.
    extensions: tuple = (
        (".py-tpl", ".py"),
        (".rst-tpl", ".rst"),
    )

    # Name of the template we are looking for (project, container, plugin, ...)
    template_prefix: str = None

    def handle(self, config: Config, name: str, target: Optional[str] = None) -> None:
        self.verbosity = config.options.verbosity
        self.validate_name(name)

        # if some directory is given, make sure it's nicely expanded
        top_dir = self.check_target_directory(target, name)

        if self.verbosity >= 2:
            terminal.line(f"Rendering {self.template_prefix} template files")

        base_name = f"{self.template_prefix}_name"
        base_subdir = f"{self.template_prefix}_template"
        base_directory = f"{self.template_prefix}_directory"
        camel_case_name = f"camel_case_{self.template_prefix}_name"
        camel_case_value = "".join(x for x in name.title() if x != "_")

        context = {
            base_name: name,
            base_directory: top_dir,
            camel_case_name: camel_case_value,
            "docs_version": get_docs_version(),
            "socon_version": socon.__version__,
        }

        template_dir = Path(socon.__path__[0], "conf", base_subdir)

        for root, dirs, files in os.walk(template_dir):
            relative_dir = str(Path(root).relative_to(template_dir))
            relative_dir = relative_dir.replace(base_name, name)

            # Make the target directory
            target_dir = Path(top_dir, relative_dir)
            os.makedirs(target_dir, exist_ok=True)

            for dirname in dirs[:]:
                # Remove __pycache__ as it's possible that when we execute a template
                # command we try to read it's content with FileReshape. This might
                # cause in the worst case a decode error.
                if dirname == "__pycache__":
                    dirs.remove(dirname)

            for filename in files:
                old_path = Path(root, filename)
                new_path = Path(top_dir, relative_dir, filename)
                for old_suffix, new_suffix in self.extensions:
                    if new_path.suffix == old_suffix:
                        new_path = new_path.with_suffix(new_suffix)

                if new_path.exists():
                    raise CommandError(
                        "{} already exists. Overlaying a {} into an existing "
                        "directory won't replace conflicting files.".format(
                            new_path,
                            self.template_prefix,
                        )
                    )

                # Render template files
                template_file = FileReshape(old_path)
                template_file.render(context)
                template_file.write(dest=new_path, encoding="utf-8")

                if self.verbosity >= 2:
                    terminal.line(f"Creating {new_path}")
                shutil.copymode(old_path, new_path)

    def check_target_directory(self, target: str, name: str) -> str:
        """
        Chech that the target directory exist. If it does not, create it.
        """
        if target is None:
            top_dir = Path.cwd().joinpath(name)
            self._make_dirs(top_dir)
        else:
            top_dir = Path(target).expanduser().absolute()
            if not top_dir.exists():
                terminal.line(
                    f"Destination directory '{top_dir}' does not "
                    "exist, we will create it for you."
                )
                self._make_dirs(top_dir)

        return top_dir

    def validate_name(self, name: str, name_or_dir: Optional[str] = "name"):
        """
        Check it's a valid directory name.
        A string is considered a valid identifier if it only contains
        alphanumeric letters (a-z) and (0-9), or underscores (_).
        A valid identifier cannot start with a number, or contain any spaces

        :param name: The name of the directory
        :param name_or_dir:
        """
        if not name.isidentifier():
            raise CommandError(
                "'{name}' is not a valid {template} {type}. Please make sure the "
                "{type} is a valid identifier.".format(
                    name=name,
                    template=self.template_prefix,
                    type=name_or_dir,
                )
            )
        # Check it cannot be imported.
        try:
            import_module(name)
        except ImportError:
            pass
        else:
            raise CommandError(
                "'{name}' conflicts with the name of an existing Python "
                "module and cannot be used as a {template} {type}. Please try "
                "another {type}.".format(
                    name=name,
                    template=self.template_prefix,
                    type=name_or_dir,
                )
            )

    @staticmethod
    def _make_dirs(directory: str) -> None:
        try:
            os.makedirs(str(directory))
        except FileExistsError:
            raise CommandError(f"'{directory}' already exists")
