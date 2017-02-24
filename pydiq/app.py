#!/usr/bin/env python
import sys

# Try imports and report missing packages.
error = False

# Just to check presence of essential libraries
from . import imports

from .imports import qtpy
from qtpy import QtCore, QtWidgets

from .viewer import Viewer

def run_app():
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
