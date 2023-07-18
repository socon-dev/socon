# SPDX-License-Identifier: BSD-3-Clause
# SPDX-License-Identifier: LicenseRef-MIT-Pytest
# Copyright (c) 2023, Stephane Capponi and Others

import shutil
import sys

from typing import Literal, Optional, TextIO, Union

color_names = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
foreground = {color_names[x]: "3%s" % x for x in range(8)}
background = {color_names[x]: "4%s" % x for x in range(8)}
decorator = {
    "reset": "0",
    "bold": "1",
    "underscore": "4",
    "blink": "5",
    "reverse": "7",
    "conceal": "8",
}


def colorize(
    msg: str, opts: Union[tuple, list] = [], fg: str = None, bg: str = None, **_: dict
) -> str:
    """
    Return your text enclosed by ANSI graphics code

    :param msg: Text message
    :param opts: Text decoration like:
        - 'bold'
        - 'underscore'
        - 'blink'
        - 'reverse'
        - 'conceal'
        - 'noreset' - string will not be auto-terminated with the RESET code

    :param fg: Foreground colors
    :param bg: Background colors

    Valid colors:
        - 'black'
        - 'red'
        - 'green'
        - 'yellow'
        - 'blue'
        - 'magenta'
        - 'cyan'
        - 'white'

    Examples:
        colorize('hello', fg='red', bg='blue', opts=('blink',))
        print(colorize('first line', fg='red', opts=('noreset',)))
        print('this should be red too')
        colorize(opts=('reset',))
        print('This will be print with default color')
    """
    markup = []

    # Do not accept None message
    if msg is None:
        msg = ""

    if len(opts) == 0 and fg is None and bg is None:
        return msg
    if msg == "" and len(opts) == 1 and opts[0] == "reset":
        return "\x1b[{}m".format(decorator["reset"])
    if fg in foreground:
        markup.append(foreground[fg])
    if bg in background:
        markup.append(background[bg])
    for o in opts:
        if o in decorator:
            markup.append(decorator[o])
    if "noreset" not in opts:
        msg = "{}\x1b[{}m".format(msg or "", decorator["reset"])
    return "{}{}".format(("\x1b[{}m".format(";".join(markup))), msg or "")


# The code below was initially copied from pytest 7.2, file src/_pytest/terminal.py.
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
        self,
        sepchar: str,
        title: Optional[str] = None,
        fullwidth: Optional[int] = None,
        newline: Optional[Literal["before", "after", "both"]] = None,
        **markup: dict,
    ) -> None:
        """
        Create a separator line with or without a title. By default the
        separator will use the fullwidth of the terminal. A specific width
        can be passed to the function if required. You can also pass the newline
        argument if you want to add a newline before, after or before and after the
        separator.

        The separator can be styled using the **markup. You can pass
        fg, bg and opts as markups.

        fg: Forground color
        bg: Background color
        opts: Text decoration

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid decorators:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            terminal.sep('-', 'colorize', fg='blue', opts=('bold',))

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

        # add a new line before
        if newline in ["before", "both"]:
            self.write("\n")

        self.line(line, **markup)

        # Add a new line after
        if newline in ["after", "both"]:
            self.write("\n")

    def write(self, msg: str, *, flush: bool = False, **markup: dict) -> None:
        """
        Write to the terminal. You can style the text using the **markup. You can pass
        fg, bg and opts as markups.

        fg: Forground color
        bg: Background color
        opts: Text decoration

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid decorators:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            terminal.write('message', fg='blue', opts=('bold',))
        """
        if msg:
            current_line = msg.rsplit("\n", 1)[-1]
            if "\n" in msg:
                self._current_line = current_line
            else:
                self._current_line += current_line

            # Apply markup style to the message
            msg = colorize(msg, **markup)

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

    def line(self, msg: str = "", **markup: dict) -> None:
        """
        Write a message that will end with a new line.
        You can style the text using the **markup. You can pass
        fg, bg and opts as markups.

        fg: Forground color
        bg: Background color
        opts: Text decoration

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid decorators:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            terminal.line('message', fg='blue', opts=('bold',))
        """
        self.write(msg, **markup)
        self.write("\n")

    def flush(self) -> None:
        self._stream.flush()

    def rewrite(self, line: str, erase: bool = False, **markup: dict) -> None:
        """
        Rewinds the terminal cursor to the beginning and writes the given line.
        You can style the text using the **markup. You can pass
        fg, bg and opts as markups.

        fg: Forground color
        bg: Background color
        opts: Text decoration

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid decorators:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            terminal.rewrite('message', fg='blue', opts=('bold',))
        """
        if erase:
            fill_count = self.fullwidth - len(line) - 1
            fill = " " * fill_count
        else:
            fill = ""
        line = str(line)
        self.write("\r" + line + fill, **markup)

    def underline(self, msg: str, decorator: str = "-", **markup: dict) -> None:
        """
        Underline a text with a decorator. You can style the text using the **markup.
        You can pass fg, bg and opts as markups.

        fg: Forground color
        bg: Background color
        opts: Text decoration

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid decorators:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            terminal.underline('message', fg='blue', opts=('bold',))
        """
        self.line(msg, **markup)
        self.line(decorator * len(msg), **markup)
        self.write("\n")


terminal = TerminalWriter()
