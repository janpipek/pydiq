import logging
from typing import Any

import numpy as np
import pydicom
from pydicom.multival import MultiValue


logger = logging.getLogger(__name__)

# Anatomical planes
TRANSVERSE = AXIAL = 0
FRONTAL = CORONAL = 1
MEDIAN = SAGITTAL = 2
ALLOWED_PLANES: tuple[int, ...] = (AXIAL, CORONAL, SAGITTAL)

# Value range shown by default for data in Hounsfield units
DEFAULT_HU_WINDOW: tuple[float, float] = (-1000.0, 3000.0)


class DicomData:
    ALLOWED_MODALITIES: tuple[str, ...] = ('CT', 'MR', 'CR', 'RT')

    # Modalities whose values are (rescaled to) Hounsfield units
    HU_MODALITIES: tuple[str, ...] = ('CT',)

    def __init__(self, data: np.ndarray, **kwargs: Any):
        self._array = data
        self.modality: str | None = kwargs.get("modality")
        # Value range (low, high) suggested by the DICOM file, if any
        self._window: tuple[float, float] | None = kwargs.get("window")

    @classmethod
    def from_files(cls, files: list[str]) -> "DicomData":
        data: list[np.ndarray] = []
        modality: str | None = None
        window: tuple[float, float] | None = None

        for file_path in files:
            logger.debug("Reading %s...", file_path)
            f = pydicom.dcmread(file_path)

            # Get modality
            if modality:
                if modality != f.Modality:
                    raise RuntimeError("Cannot mix images from different modalities")
            elif f.Modality not in cls.ALLOWED_MODALITIES:
                raise RuntimeError(f"{f.Modality} modality not supported.")
            else:
                modality = f.Modality
            if window is None:
                window = cls._read_window(f)
            data.append(cls._read_pixel_data(f))
        return cls(np.array(data), modality=modality, window=window)

    @classmethod
    def _read_pixel_data(cls, f: pydicom.Dataset) -> np.ndarray:
        if f.Modality in cls.HU_MODALITIES:
            data = f.RescaleSlope * f.pixel_array + f.RescaleIntercept
            return np.array(data)
        else:
            return np.array(f.pixel_array)

    @classmethod
    def _read_window(cls, f: pydicom.Dataset) -> tuple[float, float] | None:
        """Value range (low, high) as suggested by the DICOM file itself."""
        center = cls._first_value(f.get("WindowCenter"))
        width = cls._first_value(f.get("WindowWidth"))
        if center is None or width is None or width <= 0:
            return None
        return center - width / 2, center + width / 2

    @staticmethod
    def _first_value(value: Any) -> float | None:
        """First item of a (possibly multi-valued) numeric DICOM attribute."""
        if isinstance(value, MultiValue):
            value = value[0] if value else None
        return float(value) if value is not None else None

    @property
    def default_window(self) -> tuple[float, float]:
        """Range of values (low, high) that is reasonable to display.

        Preferably, the window stored in the DICOM file is used. Data
        in Hounsfield units (CT) have a sensible fixed fallback, for other
        modalities (MR, ...) the values are arbitrary and the window has
        to be deduced from the data themselves.
        """
        if self._window is not None:
            return self._window
        if self.modality in self.HU_MODALITIES:
            return DEFAULT_HU_WINDOW
        # Ignore a few percent of outlying voxels (noise, metal artifacts, ...)
        low, high = np.percentile(self._array, [1.0, 99.0])
        if high <= low:
            low, high = self._array.min(), self._array.max()
        return float(low), float(max(high, low + 1.0))

    @property
    def shape(self) -> tuple[int, ...]:
        return self._array.shape

    @property
    def array(self) -> np.ndarray:
        """The underlying numpy array."""
        return self._array

    def get_slice(self, plane: int, n: int) -> np.ndarray:
        if plane not in ALLOWED_PLANES:
            raise ValueError(f"Invalid plane identificator {plane} (allowed are 0, 1, 2)")
        index: list[slice | int] = [slice(None, None, None) for i in range(3)]
        index[plane] = n
        return self._array[tuple(index)]

    def get_slice_shape(self, plane: int) -> list[int]:
        # TODO: 
        shape = list(self.shape)
        shape.pop(plane)
        return shape
