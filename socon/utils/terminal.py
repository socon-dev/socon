# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-MIT-Pytest
# Copyright (c) 2023, Stephane Capponi and Others

import shutil
import sys

from typing import Optional, TextIO

# This code was initially copied from pytest 7.2, file src/_pytest/terminal.py.
# Link to the project: https://github.com/pytest-dev/pytest


def get_terminal_width() -> int:
    """Get the size of terminal"""
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanify a bit.
    if width < 40:
        width = 80

    return width


class TerminalWriter:
    """Base class to write information on the terminal"""

    def __init__(self, stream: TextIO = None) -> None:
        if stream is None:
            stream = sys.stdout
        self._current_line = ""
        self._terminal_width: Optional[int] = None
        self._stream = stream

    @property
    def fullwidth(self) -> int:
        if self._terminal_width is not None:
            return self._terminal_width
        return get_terminal_width()

    @fullwidth.setter
    def fullwidth(self, value: int) -> None:
        self._terminal_width = value

    def sep(
        self, sepchar: str, title: Optional[str] = None, fullwidth: Optional[int] = None
    ) -> None:
        """
        Create a separator line with or without a title. By default the
        separator will use the fullwidth of the terminal. A specific width
        can be passed to the function if required
        """
        if fullwidth is None:
            fullwidth = self.fullwidth
        # The goal is to have the line be as long as possible
        # under the condition that len(line) <= fullwidth.
        if sys.platform == "win32":
            # If we print in the last column on windows we are on a
            # new line but there is no way to verify/neutralize this
            # (we may not know the exact line width).
            # So let's be defensive to avoid empty lines in the output.
            fullwidth -= 1
        if title is not None:
            # we want 2 + 2*len(fill) + len(title) <= fullwidth
            # i.e.    2 + 2*len(sepchar)*N + len(title) <= fullwidth
            #         2*len(sepchar)*N <= fullwidth - len(title) - 2
            #         N <= (fullwidth - len(title) - 2) // (2*len(sepchar))
            N = max((fullwidth - len(title) - 2) // (2 * len(sepchar)), 1)
            fill = sepchar * N
            line = f"{fill} {title} {fill}"
        else:
            # we want len(sepchar)*N <= fullwidth
            # i.e.    N <= fullwidth // len(sepchar)
            line = sepchar * (fullwidth // len(sepchar))
        # In some situations there is room for an extra sepchar at the right,
        # in particular if we consider that with a sepchar like "_ " the
        # trailing space is not important at the end of the line.
        if len(line) + len(sepchar.rstrip()) <= fullwidth:
            line += sepchar.rstrip()

        self.line(line)

    def write(self, msg: str, *, flush: bool = False) -> None:
        """Write to the terminal"""
        if msg:
            current_line = msg.rsplit("\n", 1)[-1]
            if "\n" in msg:
                self._current_line = current_line
            else:
                self._current_line += current_line

            try:
                self._stream.write(msg)
            except UnicodeEncodeError:
                # Some environments don't support printing general Unicode
                # strings, due to misconfiguration or otherwise; in that case,
                # print the string escaped to ASCII.
                # When the Unicode situation improves we should consider
                # letting the error propagate instead of masking it (see #7475
                # for one brief attempt).
                msg = msg.encode("unicode-escape").decode("ascii")
                self._stream.write(msg)

            if flush:
                self.flush()

    def line(self, msg: str = "") -> None:
        """Write a message that will end with a new line"""
        self.write(msg)
        self.write("\n")

    def flush(self) -> None:
        self._stream.flush()

    def rewrite(self, line: str, erase: bool = False) -> None:
        """
        Rewinds the terminal cursor to the beginning and writes the given line.
        """
        if erase:
            fill_count = self.fullwidth - len(line) - 1
            fill = " " * fill_count
        else:
            fill = ""
        line = str(line)
        self.write("\r" + line + fill)

    def underline(self, msg: str, decorator: str = "-") -> None:
        """Underline a text with a decorator"""
        self.line(msg)
        self.line(decorator * len(msg))
        self.write("\n")


terminal = TerminalWriter()
