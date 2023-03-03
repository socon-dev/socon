from socon.core.management.base import BaseCommand, ProjectCommand


class CustomeBaseCommand(BaseCommand):
    help = "Test basic commands"
    name = "base_command"

    def add_arguments(self, parser):
        parser.add_argument("args", nargs="*")
        parser.add_argument("--option_a", "-a", default="1")
        parser.add_argument("--option_b", "-b", default="2")
        parser.add_argument("--option_c", "-c", default="3")

    def handle(self, config):
        options = vars(config.options)
        labels = options.pop("args")
        print(
            "EXECUTE:BaseCommand labels={}, options={}".format(
                tuple(labels), sorted(options.items())
            )
        )


class CommandWithoutName(BaseCommand):
    def handle(self, config):
        print(self.name)


class CommandNameEndWithCommand(BaseCommand):
    def handle(self, config):
        print(self.name)


class ReturnOutputcommand(BaseCommand):
    name = "return_output"

    def handle(self, config):
        return "foo"


class NoHandleBaseCommand(BaseCommand):
    name = "no_handle_base_cmd"


class NoHandleProjectCommand(ProjectCommand):
    name = "no_handle_pc_cmd"
