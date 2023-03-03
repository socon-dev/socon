from socon.core.management.base import BaseCommand


class CustomeExtrasArgsBaseCommand(BaseCommand):
    help = "Test basic commands with saving extra args"
    name = "extras_args_command"

    # Keep extra arguments
    keep_extras_args = True

    def handle(self, config):
        print(config.extras_args)
