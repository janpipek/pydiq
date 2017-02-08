from __future__ import division

# from ._qt import QtCore, QtWidgets, Signal, pyqtSlot
from qtpy import QtWidgets, QtCore, QtGui
from . import dicom_data


class DicomWidget(QtWidgets.QLabel):
    """Widget for displaying DICOM data.

    """
    def __init__(self, parent, **kwargs):
        # Qt initialization
        QtWidgets.QLabel.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setMouseTracking(True)

        # Inner data
        self._zoom_level = kwargs.get("zoom_level", 0)
        self._data = kwargs.get("data", None)
        self._scaled_image = None
        self._low_hu = kwargs.get("low_hu", -1000)
        self._high_hu = kwargs.get("high_hu", 3000)
        self._plane = kwargs.get("plane", dicom_data.AXIAL)
        self._slice = kwargs.get("slice", 0)
        self._color_table = kwargs.get("color_table", [QtGui.qRgb(i, i, i) for i in range(256)])

        self._image = None
        self._pixmap = None

        # Signals & slots
        self._auto_wire()

        self.update_image()

    data_changed = QtCore.Signal(name="data_changed")
    zoom_changed = QtCore.Signal(name="zoom_changed")
    calibration_changed = QtCore.Signal(name="calibration_changed")

    # == slice_changed OR plane_changed
    data_selection_changed = QtCore.Signal(name="data_selection_changed")
    slice_changed = QtCore.Signal(name="slice_changed")
    plane_changed = QtCore.Signal(name="plane_changed")

    def _auto_wire(self):
        """Wire all signals & slots that are necessary for the widget to work."""
        self.zoom_changed.connect(self.on_zoom_changed)
        self.data_changed.connect(self.on_data_changed)
        self.slice_changed.connect(self.on_data_selection_changed)
        self.plane_changed.connect(self.on_data_selection_changed)

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
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoom_changed.emit()

    def decrease_zoom(self, amount=1):
        self.zoom_level -= amount

    def increase_zoom(self, amount=1):
        self.zoom_level += amount

    def reset_zoom(self):
        self.zoom_level = 0

    @QtCore.Slot()
    def on_zoom_changed(self):
        if self._image:
            self.update_image()

    @QtCore.Slot()
    def on_data_changed(self):
        self.update_image()

    @QtCore.Slot()
    def on_calibration_changed(self):
        self.update_image()

    @QtCore.Slot()
    def on_data_selection_changed(self):
        self.update_image()

    def update_image(self):
        if self._data is not None:
            # Prepare image integer data
            raw_data = self._data.get_slice(self.plane, self.slice)
            shape = raw_data.shape
            data = (raw_data - self._low_hu) / self.window_width * 256
            data[data < 0] = 0
            data[data > 255] = 255
            data = data.astype("int8")
            self._image = QtGui.QImage(data, data.shape[1], data.shape[0], QtGui.QImage.Format_Indexed8)
            self._image.setColorTable(self._color_table)
        else:
            self._image = None
        self.update_pixmap()

    def update_pixmap(self):
        if self._image is not None:
            pixmap = QtGui.QPixmap.fromImage(self._image)
            if self.zoom_factor != 1:
                if self.zoom_factor < 1:
                    pixmap = self._pixmap.scaled(pixmap.width() * self.zoom_factor, pixmap.height() * self.zoom_factor,
                                                 QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                else:
                    pixmap = pixmap.scaled(pixmap.width() * self.zoom_factor, pixmap.height() * self.zoom_factor,
                                           QtCore.Qt.KeepAspectRatio)
            self._pixmap = pixmap
            self.setPixmap(self._pixmap)
            self.resize(pixmap.width(), pixmap.height())
        else:
            self.setText("No image.")

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, d):
        if self._data != d:
            self._data = d
            self.data_changed.emit()

    @property
    def window_center(self):
        return (self.high_hu + self.low_hu) / 2

    @window_center.setter
    def window_center(self, value):
        if value != self.window_center:
            original = self.window_center
            self._low_hu += value - original
            self._high_hu += value - original
            self.calibration_changed.emit()

    @property
    def window_width(self):
        return self._high_hu - self._low_hu

    @window_width.setter
    def window_width(self, value):
        if value < 0:
            value = 0
        original = self.window_width
        if value != original:
            self._low_hu -= (value - original) / 2
            self._high_hu = self._low_hu + value
            self.calibration_changed.emit()

    @property
    def plane(self):
        return self._plane

    @plane.setter
    def plane(self, value):
        if value != self._plane:
            if value not in [dicom_data.ALLOWED_PLANES]:
                raise ValueError("Invalid plane identificator")
            self._plane = value
            self.plane_changed.emit()
            self.data_selection_changed.emit()

    @property
    def slice(self):
        return self._slice

    @slice.setter
    def slice(self, n):
        if n != self._slice:
            self._slice = n
            self.slice_changed.emit()
            self.data_selection_changed.emit()

    @property
    def slice_count(self):
        if not self._data:
            return 0
        else:
            return self._data.shape[self.plane]