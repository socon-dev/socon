from socon.core.management.commands.createcontainer import (
    CreateContainerCommand as BaseCommand,
)


class CustomCreateContainer(BaseCommand):
    name = "custom_createcontainer"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--extra", help="An arbitrary extra value passed to the context"
        )
