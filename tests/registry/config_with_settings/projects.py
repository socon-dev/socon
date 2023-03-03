from socon.core.registry.config import ProjectConfig


class ProjectWithSettings(ProjectConfig):
    name = "registry.config_with_settings.projects"
    label = "other_settings"
    settings_module = "management.config_folder.config"


class ProjectWithWrongModule(ProjectConfig):
    name = "registry.config_with_settings.projects"
    label = "wrong_settings"
    settings_module = "No settings module"
