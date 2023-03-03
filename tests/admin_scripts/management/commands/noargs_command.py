from socon.core.management.base import BaseCommand


class NoArgsCommand(BaseCommand):
    help = "Test No-args commands"
    requires_system_checks = False
    name = "noargs_command"

    def handle(self, config):
        options = vars(config.options)
        options.pop("project")
        print("EXECUTE: noargs_command options=%s" % sorted(options.items()))
