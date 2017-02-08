#!/usr/bin/env python
import sys

# Try imports and report missing packages.
error = False

from qtpy import QtWidgets, QtCore

try:
    import dicom
except:
    print("Package pydicom not found. Please install it using pip or from https://code.google.com/p/pydicom/.")
    error = True
if error:
    sys.exit(-1)

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
