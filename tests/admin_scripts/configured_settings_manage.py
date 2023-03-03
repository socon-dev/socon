#!/usr/bin/env python
import sys

from socon.conf import global_settings, settings
from socon.core.management import execute_from_command_line

if __name__ == "__main__":
    settings.configure(global_settings, CUSTOM=1)
    execute_from_command_line(sys.argv)
