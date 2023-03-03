from socon.core.management.base import ProjectCommand


class SimpleProjectCommand(ProjectCommand):
    name = "simple_pc"

    def handle(self, config, project_config):
        print(project_config.label)


class RestrictedProjectCommand(ProjectCommand):
    name = "restricted_pc"
    projects = []

    def handle(self, config, project_config):
        pass
