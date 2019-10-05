import sys

import click
from qtpy import QtCore, QtWidgets

from pydiq.viewer import Viewer


@click.command()
@click.argument("path", required=False, type=click.Path(dir_okay=True, file_okay=False, exists=True))
def run_app(path):
    if len(sys.argv) < 2:
        path = "."
    else:
        path = sys.argv[1]

    app = QtWidgets.QApplication(sys.argv)

    QtCore.QCoreApplication.setApplicationName("pydiq")
    QtCore.QCoreApplication.setOrganizationName("Jan Pipek")

    viewer = Viewer(path)
    viewer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()