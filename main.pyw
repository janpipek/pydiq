#!/usr/bin/env python

import sys
import pydiq

try:
    from PyQt4 import QtGui, QtCore
except:
    from PySide import QtGui, QtCore

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No file specified.")
        file_name = None
    else:
        file_name = sys.argv[1]

    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setApplicationName("pydiq")
    # QtCore.QCoreApplication.setOrganizationDomain("vzdusne.cz")
    QtCore.QCoreApplication.setOrganizationName("Jan Pipek")

    viewer = pydiq.Viewer(file_name)
    viewer.show()

    sys.exit(app.exec_())
