"""
Invokes socon when the socon module is run as a script.
Example: python -m socon createproject or socon createproject
"""
from socon.core import management

if __name__ == "__main__":
    management.execute_from_command_line()
