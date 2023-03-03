# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023, Stephane Capponi and Others

from __future__ import annotations

import re

from os import PathLike
from pathlib import Path
from typing import Any, Union


class FileReshape:
    """Base class to modify the content of a file"""

    def __init__(self, filepath: Union[str, PathLike]) -> None:
        self.file = str(Path(filepath))
        with open(filepath, "r") as f:
            self.backup = f.read()
        self.content = self.backup

    def __eq__(self, o: FileReshape) -> bool:
        return self.content == o.content

    def revert_modif(self) -> None:
        """Revert the modification applied in the file"""
        self.content = self.backup
        self.write(self.backup)

    def reshape(self, **kwargs: Any) -> None:
        """Write all modification to the file"""
        self.write(self.content, **kwargs)

    def write(
        self, content: str = None, dest: Union[str, Path] = None, **kwargs: Any
    ) -> None:
        """
        Write content to the current file or to a another file using the ``dest``
        parameter. This method also allow to pass any parameters to the open
        function.
        """
        content = self.content if content is None else content
        dest = self.file if dest is None else dest
        with open(str(dest), "w", **kwargs) as f:
            f.write(content)

    def replace(self, pattern: str, replace: str, **kwargs) -> None:
        """Replace any string that match the pattern"""
        self.content = re.sub(pattern, replace, self.content, **kwargs)

    def read_file(self) -> None:
        """Read the content of the file"""
        for line in open(self.file, "r"):
            print(line, end="")

    def render(self, context: dict) -> str:
        """Render a specific template with tag like {{ value }}"""
        search_tag = re.findall(r"({{ (.*) }})", self.content)
        if search_tag:
            self.content = self._compile(search_tag, context)
        return self.content

    def _compile(self, tag_found: str, context: dict) -> str:
        """Replace the tag found by the context value"""
        content = self.content
        for tag, value in tag_found:
            for option, var in context.items():
                if option == value:
                    content = content.replace(tag, str(var))
        return content
