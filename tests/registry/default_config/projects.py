from socon.core.registry.config import ProjectConfig


class BadConfig(ProjectConfig):
    """This class doesn't supply the mandatory 'name' attribute."""


class NotAConfig:
    name = "myprojects"


class NoSuchProject(ProjectConfig):
    name = "there is no such project"


class PlainProjectsConfig(ProjectConfig):
    name = "registry.default_config.projects"


class RelabeledProjectsConfig(ProjectConfig):
    name = "registry.default_config.projects"
    label = "relabeled"
