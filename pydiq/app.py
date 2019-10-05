#!/usr/bin/env python
from qtpy import QtCore, QtWidgets

from pydiq.viewer import Viewer


def run_app():
    import sys
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

