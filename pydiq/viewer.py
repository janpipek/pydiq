import logging
import os
from typing import Any

from qtpy import QtWidgets, QtCore, QtGui

import pydicom


from pydiq.dicom_data import AXIAL, DicomData
from pydiq.dicom_widget import DicomWidget
from pydiq.utils import dicom_files_in_dir


logger = logging.getLogger(__name__)


class Viewer(QtWidgets.QMainWindow):
    def __init__(self, path: str = "."):
        super(Viewer, self).__init__()
        self.setWindowTitle("pydiq - Python DICOM Viewer in Qt")
        self.file: pydicom.Dataset | None = None
        self._file_name: str | None = None

        self.high_hu = 2000
        self.low_hu = -1024
       
        # self.pix_label = TrackingLabel(self)
        self.pix_label = DicomWidget(self)

        # self.color_table = [QtWidgets.qRgb(i, i, i) for i in range(256)]

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(self.pix_label)

        # self.setCentralWidget(self.pix_label)
        self.setCentralWidget(scroll_area)

        self.series_dock = QtWidgets.QDockWidget("Series", self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.series_dock)

        self.file_dock = QtWidgets.QDockWidget("Images", self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.file_dock)

        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_item_change)
        self.file_dock.setWidget(self.file_list)

        self.series_list = QtWidgets.QListWidget()
        # self.studies_list.itemSelectionChanged.connect(self.on_study_item_change)
        self.series_dock.setWidget(self.series_list)

        self.name_label = QtWidgets.QLabel("")
        self.hu_label = QtWidgets.QLabel("No image")
        self.cw_label = QtWidgets.QLabel("")
        self.x_label = QtWidgets.QLabel("")
        self.y_label = QtWidgets.QLabel("")
        self.z_label = QtWidgets.QLabel("")
        self.use_fractional_coordinates: bool = True
        self.ij_label = QtWidgets.QLabel("")

        self.mouse_x: int = -1
        self.mouse_y: int = -1

        # The name of the image on the left, the readouts on the right
        self.statusBar().addWidget(self.name_label)
        self.statusBar().addPermanentWidget(self.cw_label)
        self.statusBar().addPermanentWidget(self.ij_label)
        self.statusBar().addPermanentWidget(self.x_label)
        self.statusBar().addPermanentWidget(self.y_label)
        self.statusBar().addPermanentWidget(self.z_label)
        self.statusBar().addPermanentWidget(self.hu_label)

        self.pix_label.data_changed.connect(self.update_cw)
        self.pix_label.calibration_changed.connect(self.update_cw)
        self.pix_label.data_changed.connect(self.update_coordinates)
        self.pix_label.data_selection_changed.connect(self.update_coordinates)
        self.update_cw()

        if os.path.isfile(path):
            self.load_files([path])
        elif os.path.isdir(path):
            self.load_files(dicom_files_in_dir(path))
        self.build_menu()

    def open_directory(self) -> None:
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.List)
        dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec_():
            directory = str(dialog.selectedFiles()[0])
            self.load_files(dicom_files_in_dir(directory))

    def export_image(self) -> None:
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save file",
            os.path.expanduser("~/dicom-export.png"),
            "PNG images (*.png)"
        )
        if file_name:
            self.pix_label._image.save(file_name)

    def build_menu(self) -> None:
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Open directory', self.open_directory, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_O)
        self.file_menu.addAction('&Export image', self.export_image, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_S)
        self.file_menu.addAction('&Quit', self.close, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_Q)      

        self.view_menu = QtWidgets.QMenu('&View', self)
        self.view_menu.addAction('Zoom In', self.pix_label.increase_zoom, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_Plus)
        self.view_menu.addAction('Zoom Out', self.pix_label.decrease_zoom, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_Minus)
        self.view_menu.addAction('Zoom 1:1', self.pix_label.reset_zoom, QtCore.Qt.Modifier.CTRL | QtCore.Qt.Key.Key_0)
        fullscreen = QtWidgets.QAction('&Full Screen', self)
        fullscreen.setCheckable(True)
        fullscreen.setShortcut(QtCore.Qt.Key.Key_F11)
        fullscreen.toggled.connect(self.toggle_full_screen)
        self.view_menu.addAction(fullscreen)

        self.tools_menu = QtWidgets.QMenu("&Tools", self)
        self.tools_menu.addAction('&Show DICOM structure', self.show_structure, QtCore.Qt.Key.Key_F2)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.tools_menu)

    def show_structure(self) -> None:
        if not self.file_name:
            return
        try:
            # pydicom parses lazily, so rendering can fail even if reading did not
            structure = str(pydicom.dcmread(self.file_name))
        except Exception:
            logger.exception("Could not read the structure of %s", self.file_name)
            self.statusBar().showMessage("Could not read the DICOM structure.", 5000)
            return

        # The dialog is parented to the viewer, so that Qt keeps it alive
        # for as long as it is open (and destroys it once closed).
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"DICOM structure: {os.path.basename(self.file_name)}")
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.resize(800, 600)

        text = QtWidgets.QPlainTextEdit(structure, dialog)
        text.setReadOnly(True)
        text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        text.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont))

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(text)
        dialog.show()

    def toggle_full_screen(self, toggled: bool) -> None:
        if toggled:
            self.setWindowState(QtCore.Qt.WindowState.WindowFullScreen)
        else:
            self.setWindowState(QtCore.Qt.WindowState.WindowNoState)

    def on_file_item_change(self) -> None:
        if not len(self.file_list.selectedItems()):
            self.file_name = None
        else:
            item = self.file_list.selectedItems()[0]
            self.file_name = str(item.toolTip())

    def load_files(self, files: list[str]) -> None:
        self.series_list.clear()
        self.series: dict[str, Any] = {}


        self.file_list.clear()
        self.files: list[str] = files
        for file_name in self.files:
            item = QtWidgets.QListWidgetItem(os.path.basename(file_name))
            item.setToolTip(file_name)
            self.file_list.addItem(item)
        self.file_list.setMinimumWidth(self.file_list.sizeHintForColumn(0) + 20)
        if self.files:
            self.file_name = self.files[0]


    @property
    def zoom_factor(self) -> float:
        """Real size of a data voxel in screen pixels."""
        return self.pix_label.zoom_factor

    def get_coordinates(self, row: float, column: float) -> tuple[float, float, float]:
        """DICOM patient coordinates (in mm) of a position in the shown slice."""
        data = self.pix_label.data
        if data is None:
            raise ValueError("No image loaded.")
        # Put the slice back into the index to address the whole stack,
        # exactly the way DicomData.get_slice took it out.
        index: list[float] = [row, column]
        index.insert(self.pix_label.plane, self.pix_label.slice)
        return data.voxel_position(int(index[0]), index[1], index[2])

    @property
    def mouse_position(self) -> tuple[float, float] | None:
        '''Mouse position as continuous (row, column) in the current slice.'''
        return self.pix_label.voxel_at(self.mouse_x, self.mouse_y)

    @property
    def mouse_ij(self) -> tuple[int, int] | None:
        '''Mouse position as (row, column) voxel index in current DICOM slice.'''
        position = self.mouse_position
        if position is None:
            return None
        return int(position[0]), int(position[1])

    def coordinates_of(self, position: tuple[float, float]) -> tuple[float, float, float]:
        '''DICOM coordinates of a continuous (row, column) in the shown slice.'''
        row, column = position
        if self.use_fractional_coordinates:
            # To get the center of the left top pixel in a zoom grid
            correction = (self.zoom_factor - 1.) / (2. * self.zoom_factor)
            return self.get_coordinates(row - correction, column - correction)
        else:
            return self.get_coordinates(int(row), int(column))

    @property
    def mouse_xyz(self) -> tuple[float, float, float] | None:
        '''Mouse position in DICOM coordinates, None if not on the image.'''
        position = self.mouse_position
        return None if position is None else self.coordinates_of(position)

    def update_coordinates(self) -> None:
        data = self.pix_label.data
        if data is None:
            self.z_label.setText("")
            self._clear_cursor_labels()
            self.hu_label.setText("No image")
            return

        # In an axial view the whole slice shares one z, so it stays readable
        # wherever the mouse happens to be. In the other planes z varies
        # across the image and is only known under the cursor.
        slice_z = self.slice_z
        self.z_label.setText("" if slice_z is None else f"z: {slice_z:.2f}")

        position = self.mouse_position
        if position is None:
            # The cursor is not on the image - the surroundings of the image
            # are not voxels and have no position or value to report.
            self._clear_cursor_labels()
            return

        i, j = int(position[0]), int(position[1])
        slice_data = data.get_slice(self.pix_label.plane, self.pix_label.slice)
        x, y, z = self.coordinates_of(position)
        self.x_label.setText(f"x: {x:.2f}")
        self.y_label.setText(f"y: {y:.2f}")
        self.z_label.setText(f"z: {z:.2f}")
        self.ij_label.setText(f"Pos: ({i}, {j})")
        self.hu_label.setText(f"{self.value_name}: {slice_data[i, j]:.0f}")

    @property
    def slice_z(self) -> float | None:
        """z of the displayed slice, if the whole slice shares a single one."""
        data = self.pix_label.data
        if data is None or self.pix_label.plane != AXIAL:
            return None
        return data.voxel_position(self.pix_label.slice, 0, 0)[2]

    def _clear_cursor_labels(self) -> None:
        """Blank the readouts that only mean something under the cursor."""
        for label in (self.ij_label, self.x_label, self.y_label, self.hu_label):
            label.setText("")

    @property
    def value_name(self) -> str:
        """How to call the voxel values of the currently shown image."""
        data = self.pix_label.data
        return "HU" if data is not None and data.uses_hounsfield_units else "Value"

    def update_cw(self) -> None:
        if self.pix_label.data is None:
            self.cw_label.setText("")
        else:
            self.cw_label.setText(
                f"W: {self.pix_label.window_width:.0f} C: {self.pix_label.window_center:.0f}"
            )

    @property
    def file_name(self) -> str | None:
        return self._file_name

    @file_name.setter
    def file_name(self, value: str | None) -> None:
        self._file_name = value
        if value is None:
            self._show_no_image()
        else:
            try:
                self.pix_label.data = DicomData.from_files([value])
                self.setWindowTitle(f"pydiq: {value}")
                self.name_label.setText(os.path.basename(value))
            except BaseException:
                logger.exception("Could not load image from %s", value)
                self._show_no_image()
        self.update_coordinates()

    def _show_no_image(self) -> None:
        self.pix_label.data = None
        self.setWindowTitle("pydiq: No image")
        self.name_label.setText("")

