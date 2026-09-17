import logging
import sys

import click
from qtpy import QtCore, QtWidgets

from pydiq.viewer import Viewer


LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]


def configure_logging(verbosity: int) -> None:
    """Send log messages to stderr, the more `-v`'s the more of them."""
    level = LOG_LEVELS[min(verbosity, len(LOG_LEVELS) - 1)]
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )


@click.command()
@click.argument(
    "path", required=False, default=".",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
)
@click.option(
    "-v", "--verbose", "verbosity", count=True,
    help="Increase logging verbosity (-v for info, -vv for debug).",
)
def run_app(path: str, verbosity: int) -> None:
    configure_logging(verbosity)

    app = QtWidgets.QApplication(sys.argv)

    QtCore.QCoreApplication.setApplicationName("pydiq")
    QtCore.QCoreApplication.setOrganizationName("Jan Pipek")

    viewer = Viewer(path)
    viewer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
