#!/usr/bin/env python
import sys

# Try imports and report missing packages.
error = False
try:
    from PyQt4 import QtGui, QtCore
except:
    try:
        from PySide import QtGui, QtCore
    except:
        print "No Qt4 bindings found. Please install either PyQt4 or PySide."
        error = True
try:
    import dicom
except:
    print "Package pydicom not found. Please install it using pip or from https://code.google.com/p/pydicom/."
    error = True
if error:
    sys.exit(-1)

from viewer import Viewer

def run_app():
    if len(sys.argv) < 2:
        path = "."
    else:
        path = sys.argv[1]

    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setApplicationName("pydiq")
    QtCore.QCoreApplication.setOrganizationName("Jan Pipek")

    viewer = Viewer(path)
    viewer.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()