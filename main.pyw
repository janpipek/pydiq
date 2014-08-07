#!/usr/bin/env python

import sys
import pydiq

try:
    from PyQt4 import QtGui, QtCore
except:
    from PySide import QtGui, QtCore

if __name__ == "__main__":
    if len(sys.argv) < 2:
        path = "."
    else:
        path = sys.argv[1]

    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setApplicationName("pydiq")
    QtCore.QCoreApplication.setOrganizationName("Jan Pipek")

    viewer = pydiq.Viewer(path)
    viewer.show()

    sys.exit(app.exec_())
