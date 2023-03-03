from socon.core.management.base import ProjectCommand


class SimpleCommand(ProjectCommand):
    name = "simple_command"

    def handle(self, config, project_config):
        pass
