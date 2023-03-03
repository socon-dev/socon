from socon.core.registry.config import ProjectConfig


class ProjectWithError(ProjectConfig):
    name = "admin_scripts.project_with_error"


# Write this here to throw an error when importing the project
raise ImportError("Test import error")
