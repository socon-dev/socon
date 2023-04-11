import os

from pathlib import Path
from unittest import mock

import pytest

from socon.core.exceptions import CommandNotFound
from socon.core.management import ManagementUtility, call_command
from socon.core.management.base import CommandError
from socon.test.utils import override_settings


@override_settings(
    INSTALLED_PROJECTS=[
        "user_commands",
    ],
)
class CommandTests:
    def test_project_command(self, capsys):
        """Check call_command on a project command"""
        call_command("launch", "--project", "user_commands", "-s", "Orion")
        captured = capsys.readouterr()
        assert captured.out == "Launching Orion\n"

    def test_general_command(self, test_dir):
        """Check call_command on an admin command"""
        call_command("createcontainer", "test_container", "--target", str(test_dir))
        assert Path(test_dir, "test_container").exists() is True

    def test_call_command_option_parsing_non_string_arg(self, capsys):
        """
        It should be possible to pass non-string arguments to call_command.
        """
        call_command("launch", 1, "--project", "user_commands")
        captured = capsys.readouterr()
        assert captured.out == "You passed 1 as a positional argument.\n"

    def test_unknown_command(self):
        """Check that we correctly raise CommandNotFound"""
        with pytest.raises(CommandNotFound):
            call_command("unknown")

    def test_system_exit(self, capsys):
        """
        Exception raised in a command should raise CommandError with
        call_command, but SystemExit when run from command line
        """
        with pytest.raises(CommandError) as cm:
            call_command("launch", "--example", "raise", "--project", "user_commands")
            assert cm.exception.returncode == 3
        try:
            with pytest.raises(SystemExit) as cm:
                ManagementUtility(
                    [
                        "manage.py",
                        "launch",
                        "--example=raise",
                        "--project",
                        "user_commands",
                    ]
                ).execute()
                assert cm.exception.code == 3
        finally:
            captured = capsys.readouterr()
        assert "CommandError" in captured.err

    @override_settings(
        INSTALLED_PROJECTS=["user_commands", "admin_scripts.project_with_command"],
    )
    @mock.patch.dict(os.environ, {"SOCON_ACTIVE_PROJECT": "user_commands"})
    def test_call_command_of_another_project(self):
        """
        Call a command from any project without changing the current active project
        """
        assert os.environ.get("SOCON_ACTIVE_PROJECT") == "user_commands"
        output = call_command("simple_command", "--project", "project_with_command")
        assert output == "project_with_command"
        assert os.environ.get("SOCON_ACTIVE_PROJECT") == "user_commands"

    def test_call_command_keep_extras_args(self, capsys):
        """
        Check that we correctly save the extras args of the command in the config
        object
        """
        extras_args = ["-e", "extras"]
        call_command("launch_extras", "--project", "user_commands", *extras_args)
        captured = capsys.readouterr()
        assert captured.out == "Extras args = {}\n".format(extras_args)

    def test_call_command_project_index_error(self):
        """
        Raise CommandError if the user didn't pass a project. Let the
        parser do the job and throw an error that the project does not exist.
        """
        with pytest.raises(CommandError):
            call_command("launch", "--project")
        with pytest.raises(CommandError):
            call_command("launch", "--project", "foo")
