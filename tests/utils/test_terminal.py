import io
import shutil
import sys

from io import StringIO
from pathlib import Path
from typing import Generator
from unittest import mock

import pytest

from pytest import MonkeyPatch

from socon.utils import terminal
from socon.utils.terminal import TerminalWriter

# This code was initially copied from pytest 7.2, file src/_pytest/terminal.py.
# Link to the project: https://github.com/pytest-dev/pytest


def test_terminal_width_COLUMNS(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "42")
    assert terminal.get_terminal_width() == 42
    monkeypatch.delenv("COLUMNS", raising=False)


def test_terminalwriter_width_bogus(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "get_terminal_size", mock.Mock(return_value=(10, 10)))
    monkeypatch.delenv("COLUMNS", raising=False)
    tw = terminal.TerminalWriter()
    assert tw.fullwidth == 80


def test_terminalwriter_computes_width(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(terminal, "get_terminal_width", lambda: 42)
    tw = terminal.TerminalWriter()
    assert tw.fullwidth == 42


def test_terminalwriter_not_unicode() -> None:
    """If the file doesn't support Unicode, the string is unicode-escaped (#7475)."""
    buffer = io.BytesIO()
    file = io.TextIOWrapper(buffer, encoding="cp1252")
    tw = terminal.TerminalWriter(file)
    tw.write("hello 🌀 wôrld אבג", flush=True)
    assert buffer.getvalue() == rb"hello \U0001f300 w\xf4rld \u05d0\u05d1\u05d2"


win32 = int(sys.platform == "win32")


class TerminalWriterTests:
    @pytest.fixture(params=["path", "stringio"])
    def tw(self, request, test_dir: Path) -> Generator[TerminalWriter, None, None]:
        if request.param == "path":
            p = test_dir.joinpath("tmpfile")
            f = open(str(p), "w+", encoding="utf8")
            tw = TerminalWriter(f)

            def getlines():
                f.flush()
                with open(str(p), encoding="utf8") as fp:
                    return fp.readlines()

        elif request.param == "stringio":
            f = StringIO()
            tw = TerminalWriter(f)

            def getlines():
                f.seek(0)
                return f.readlines()

        tw.getlines = getlines  # type: ignore
        tw.getvalue = lambda: "".join(getlines())  # type: ignore

        with f:
            yield tw

    def test_line(self, tw) -> None:
        tw.line("hello")
        lines = tw.getlines()
        assert len(lines) == 1
        assert lines[0] == "hello\n"

    def test_line_unicode(self, tw) -> None:
        msg = "b\u00f6y"
        tw.line(msg)
        lines = tw.getlines()
        assert lines[0] == msg + "\n"

    def test_sep_no_title(self, tw) -> None:
        tw.sep("-", fullwidth=60)
        lines = tw.getlines()
        assert len(lines) == 1
        assert lines[0] == "-" * (60 - win32) + "\n"

    def test_sep_with_title(self, tw) -> None:
        tw.sep("-", "hello", fullwidth=60)
        lines = tw.getlines()
        assert len(lines) == 1
        assert lines[0] == "-" * 26 + " hello " + "-" * (27 - win32) + "\n"

    @mock.patch("sys.platform", "linux")
    def test_sep_not_win32_terminal(self, tw):
        tw.sep("-", "hello", fullwidth=60)
        lines = tw.getlines()
        assert len(lines) == 1
        assert lines[0] == "-" * 26 + " hello " + "-" * (27) + "\n"

    def test_sep_longer_than_width(self, tw) -> None:
        tw.sep("-", "a" * 10, fullwidth=5)
        (line,) = tw.getlines()
        # even though the string is wider than the line, still have a separator
        assert line == "- aaaaaaaaaa -\n"

    def test_rewrite_with_erase(self) -> None:
        f = StringIO()
        tr = TerminalWriter(f)
        tr.fullwidth = 10
        tr.write("hello")
        tr.rewrite("hey", erase=True)
        assert f.getvalue() == "hello" + "\r" + "hey" + (6 * " ")

    def test_rewrite_no_erase(self) -> None:
        f = StringIO()
        tr = TerminalWriter(f)
        tr.fullwidth = 10
        tr.write("hello")
        tr.rewrite("hey")
        assert f.getvalue() == "hello\rhey"

    def test_attr_fullwidth(self, tw) -> None:
        tw.sep("-", "hello", fullwidth=70)
        tw.fullwidth = 70
        tw.sep("-", "hello")
        lines = tw.getlines()
        assert len(lines[0]) == len(lines[1])

    def test_write_no_msg(self, tw) -> None:
        f = StringIO()
        tr = TerminalWriter(f)
        tr.write("")
        assert f.getvalue() == ""
