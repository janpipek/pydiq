from typing import TYPE_CHECKING, Any

from qtpy import QtWidgets, QtCore, QtGui

from pydiq.dicom_data import DicomData, AXIAL, ALLOWED_PLANES, DEFAULT_HU_WINDOW

if TYPE_CHECKING:
    from pydiq.viewer import Viewer


class TrackingLabel(QtWidgets.QLabel):
    window: "Viewer"

    def __init__(self, parent: "Viewer", **kwargs: Any):
        super(TrackingLabel, self).__init__(parent)
        self.setMouseTracking(True)
        self.last_move_x: int | None = None
        self.last_move_y: int | None = None
        self.window = parent

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.window.mouse_x = -1
        self.window.mouse_y = -1
        self.window.update_coordinates()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        position = event.position().toPoint()
        self.window.mouse_x = position.x()
        self.window.mouse_y = position.y()
        self.window.update_coordinates()

        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if self.last_move_x is not None and self.last_move_y is not None:
                self.window_width += position.y() - self.last_move_y
                self.window_center += position.x() - self.last_move_x

            self.last_move_x = position.x()
            self.last_move_y = position.y()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        position = event.position().toPoint()
        self.last_move_x = position.x()
        self.last_move_y = position.y()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.last_move_x = None
        self.last_move_y = None

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        file_list = self.window.file_list
        if len(file_list.selectedItems()):
            index = file_list.row(file_list.selectedItems()[0])
        else:
            index = -1
        if event.pixelDelta().y() > 0:
            index -= 1
        else:
            index += 1

        if index >= file_list.count() or index == -2:
            index = file_list.count() - 1
        elif index < 0:
            index = 0

        file_list.setCurrentItem(file_list.item(index))


class DicomWidget(TrackingLabel):
    """Widget for displaying DICOM data.

    """
    def __init__(self, parent: "Viewer", **kwargs: Any):
        # Qt initialization
        super(DicomWidget, self).__init__(parent, **kwargs)
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        # Inner data
        self._zoom_level: int = kwargs.get("zoom_level", 0)
        self._data: DicomData | None = kwargs.get("data", None)
        self._scaled_image: QtGui.QImage | None = None
        self._low_value: float = kwargs.get("low_value", DEFAULT_HU_WINDOW[0])
        self._high_value: float = kwargs.get("high_value", DEFAULT_HU_WINDOW[1])
        self._plane: int = kwargs.get("plane", AXIAL)
        self._slice: int = kwargs.get("slice", 0)
        self._color_table: list[int] = kwargs.get("color_table", [QtGui.qRgb(i, i, i) for i in range(256)])

        self._image: QtGui.QImage | None = None
        self._pixmap: QtGui.QPixmap | None = None

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

    def _auto_wire(self) -> None:
        """Wire all signals & slots that are necessary for the widget to work."""
        self.zoom_changed.connect(self.on_zoom_changed)
        self.data_changed.connect(self.on_data_changed)
        self.calibration_changed.connect(self.on_calibration_changed)
        self.slice_changed.connect(self.on_data_selection_changed)
        self.plane_changed.connect(self.on_data_selection_changed)

    def image_rect(self) -> QtCore.QRect | None:
        """The part of the widget the image is actually drawn on.

        The widget is not necessarily the same size as the image, and the
        label aligns the pixmap inside it rather than filling it.
        """
        pixmap = self.pixmap()
        if pixmap is None or pixmap.isNull():
            return None
        return QtWidgets.QStyle.alignedRect(
            self.layoutDirection(),
            self.alignment(),
            pixmap.deviceIndependentSize().toSize(),
            self.contentsRect(),
        )

    def voxel_at(self, x: int, y: int) -> tuple[float, float] | None:
        """Continuous (row, column) in the data of a point in the widget.

        None if the point is not on the image, so that the surroundings of
        the image do not get reported as if they were part of it.
        """
        if self._data is None:
            return None
        rect = self.image_rect()
        if rect is None or not rect.contains(x, y):
            return None
        row = (y - rect.top()) / self.zoom_factor
        column = (x - rect.left()) / self.zoom_factor
        rows, columns = self._data.get_slice_shape(self.plane)
        if not (0 <= row < rows and 0 <= column < columns):
            return None
        return row, column

    @property
    def zoom_level(self) -> int:
        """Zoom level.

        An integer value useful for the GUI
        0 = 1:1, positive values = zoom in, negative values = zoom out
        """
        return self._zoom_level

    @zoom_level.setter
    def zoom_level(self, value: int) -> None:
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoom_changed.emit()

    @property
    def zoom_factor(self) -> float:
        """Real size of data voxel in screen pixels."""
        if self._zoom_level > 0:
            return self._zoom_level + 1
        else:
            return 1.0 / (1 - self._zoom_level)

    def decrease_zoom(self, amount: int = 1) -> None:
        self.zoom_level -= amount

    def increase_zoom(self, amount: int = 1) -> None:
        self.zoom_level += amount

    def reset_zoom(self) -> None:
        self.zoom_level = 0

    @QtCore.Slot()
    def on_zoom_changed(self) -> None:
        if self._image:
            self.update_image()

    @QtCore.Slot()
    def on_data_changed(self) -> None:
        self.reset_calibration()
        self.update_image()

    @QtCore.Slot()
    def on_calibration_changed(self) -> None:
        self.update_image()

    @QtCore.Slot()
    def on_data_selection_changed(self) -> None:
        self.update_image()

    def update_image(self) -> None:
        if self._data is not None:
            # Prepare image integer data
            raw_data = self._data.get_slice(self.plane, self.slice)
            data = ((raw_data - self._low_value) / self.window_width * 256).clip(0, 255).astype("uint8")
            # copy() because QImage does not take ownership of the numpy buffer
            self._image = QtGui.QImage(
                data, data.shape[1], data.shape[0], data.strides[0], QtGui.QImage.Format.Format_Indexed8
            ).copy()
            self._image.setColorTable(self._color_table)
        else:
            self._image = None
        self.update_pixmap()

    def update_pixmap(self) -> None:
        if self._image is not None:
            pixmap = QtGui.QPixmap.fromImage(self._image)
            if self.zoom_factor != 1:
                if self.zoom_factor < 1:
                    pixmap = self._pixmap.scaled(pixmap.width() * self.zoom_factor, pixmap.height() * self.zoom_factor,
                                                 QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                else:
                    pixmap = pixmap.scaled(pixmap.width() * self.zoom_factor, pixmap.height() * self.zoom_factor,
                                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self._pixmap = pixmap
            self.setPixmap(self._pixmap)
            self.resize(pixmap.width(), pixmap.height())
        else:
            self.setText("No image.")

    @property
    def data(self) -> DicomData | None:
        return self._data

    @data.setter
    def data(self, d: DicomData | None) -> None:
        if self._data != d:
            self._data = d
            self.data_changed.emit()

    @property
    def window_center(self) -> float:
        """Center of the displayed value range (in HU for CT data)."""
        return (self._high_value + self._low_value) / 2

    @window_center.setter
    def window_center(self, value: float) -> None:
        if value != self.window_center:
            original = self.window_center
            self._low_value += value - original
            self._high_value += value - original
            self.calibration_changed.emit()

    @property
    def window_width(self) -> float:
        """Width of the displayed value range (in HU for CT data)."""
        return self._high_value - self._low_value

    @window_width.setter
    def window_width(self, value: float) -> None:
        if value < 0:
            value = 0
        original = self.window_width
        if value != original:
            self._low_value -= (value - original) / 2
            self._high_value = self._low_value + value
            self.calibration_changed.emit()

    def reset_calibration(self) -> None:
        """Set the displayed value range to one sensible for the current data."""
        low, high = self._data.default_window if self._data is not None else DEFAULT_HU_WINDOW
        if (low, high) != (self._low_value, self._high_value):
            self._low_value = low
            self._high_value = high
            self.calibration_changed.emit()

    @property
    def plane(self) -> int:
        return self._plane

    @plane.setter
    def plane(self, value: int) -> None:
        if value != self._plane:
            if value not in ALLOWED_PLANES:
                raise ValueError("Invalid plane identificator")
            self._plane = value
            self.plane_changed.emit()
            self.data_selection_changed.emit()

    @property
    def slice(self) -> int:
        return self._slice

    @slice.setter
    def slice(self, n: int) -> None:
        if n != self._slice:
            self._slice = n
            self.slice_changed.emit()
            self.data_selection_changed.emit()

    @property
    def slice_count(self) -> int:
        if not self._data:
            return 0
        else:
            return self._data.shape[self.plane]
