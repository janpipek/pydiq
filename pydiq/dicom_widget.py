from __future__ import division

from ._qt import QtCore, QtGui, pyqtSignal, pyqtSlot

class DicomWidget(QtGui.QLabel):
    """Widget for displaying DICOM data."""

    def __init__(self, parent, **kwargs):
        # Qt initialization
        QtGui.QLabel.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setMouseTracking(True)

        # Inner data
        self._zoom_level = kwargs.get("zoom_level", 0)

    def _auto_wire(self):

        # TODO
        pass

    zoom_changed = pyqtSignal()

    @property
    def zoom_level(self):
        """Zoom level.

        An integer value useful for the GUI
        0 = 1:1, positive values = zoom in, negative values = zoom out
        """
        return self._zoom_level

    @property
    def zoom_factor(self):
        """Real size of data voxel in screen pixels."""
        if self._zoom_level > 0:
            return self._zoom_level + 1
        else:
            return 1.0 / (1 - self._zoom_level)

    @zoom_level.setter
    def zoom_level(self, value):
        self._zoom_level = value
