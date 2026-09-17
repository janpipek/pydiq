import logging
from typing import Any

import numpy as np
import pydicom
from pydicom.multival import MultiValue
from pydicom.pixels import apply_color_lut, convert_color_space, get_decoder


logger = logging.getLogger(__name__)

# Anatomical planes
TRANSVERSE = AXIAL = 0
FRONTAL = CORONAL = 1
MEDIAN = SAGITTAL = 2
ALLOWED_PLANES: tuple[int, ...] = (AXIAL, CORONAL, SAGITTAL)

# Value range shown by default for data in Hounsfield units
DEFAULT_HU_WINDOW: tuple[float, float] = (-1000.0, 3000.0)

# Used when the DICOM file says nothing about the image geometry
DEFAULT_PIXEL_SPACING: tuple[float, float] = (1.0, 1.0)
DEFAULT_IMAGE_POSITION: tuple[float, float, float] = (0.0, 0.0, 0.0)


class DicomData:
    ALLOWED_MODALITIES: tuple[str, ...] = ('CT', 'MR', 'CR', 'RT', 'NM', 'US', 'OT')

    # Modalities whose values are (rescaled to) Hounsfield units
    HU_MODALITIES: tuple[str, ...] = ('CT',)

    # Ways of storing samples that can be shown as they are
    GRAYSCALE_INTERPRETATIONS: tuple[str, ...] = ('MONOCHROME1', 'MONOCHROME2')

    def __init__(self, data: np.ndarray, **kwargs: Any):
        self._array = data
        self.modality: str | None = kwargs.get("modality")
        # Value range (low, high) suggested by the DICOM file, if any
        self._window: tuple[float, float] | None = kwargs.get("window")
        # Physical size of a voxel (row, column) in mm, if the files say
        spacing: tuple[float, float] | None = kwargs.get("pixel_spacing")
        self.has_pixel_spacing: bool = spacing is not None
        self.pixel_spacing: tuple[float, float] = spacing or DEFAULT_PIXEL_SPACING
        # Patient coordinates (x, y, z) of the first voxel of each slice
        positions: list[tuple[float, float, float] | None] | None = kwargs.get("image_positions")
        if positions is None:
            positions = [None] * len(self._array)
        # Images that do not say where they are get stacked at the origin,
        # but the viewer should not report that as if it were measured.
        self.has_image_positions: bool = any(position is not None for position in positions)
        self.image_positions: np.ndarray = np.asarray(
            [position or DEFAULT_IMAGE_POSITION for position in positions], dtype=float
        ).reshape(-1, 3)
        if len(self.image_positions) != len(self._array):
            raise ValueError(
                f"Got {len(self.image_positions)} image positions "
                f"for {len(self._array)} slices."
            )

    @classmethod
    def from_files(cls, files: list[str]) -> "DicomData":
        data: list[np.ndarray] = []
        modality: str | None = None
        window: tuple[float, float] | None = None
        pixel_spacing: tuple[float, float] | None = None
        image_positions: list[tuple[float, float, float] | None] = []

        for file_index, file_path in enumerate(files):
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
            # In-plane spacing is assumed to be the same for the whole stack,
            # but each slice sits at its own position.
            if file_index == 0:
                pixel_spacing = cls._read_pixel_spacing(f)
            # A file holds one image per frame - most hold exactly one.
            frames = cls._read_pixel_data(f)
            data.extend(frames)
            image_positions.extend(
                cls._read_image_position(f, frame) for frame in range(len(frames))
            )
        return cls(
            np.array(data),
            modality=modality,
            window=window,
            pixel_spacing=pixel_spacing,
            image_positions=image_positions,
        )

    @classmethod
    def _read_pixel_data(cls, f: pydicom.Dataset) -> np.ndarray:
        """Images of one file as a (frame, row, column) array.

        Colour images keep a trailing axis of three RGB samples. A
        single-frame file yields a stack of one, so that nothing
        downstream has to know how many frames a file happened to hold.
        """
        array, interpretation = cls._decode(f)
        is_color = interpretation not in cls.GRAYSCALE_INTERPRETATIONS
        if is_color:
            array = cls._to_rgb(array, f, interpretation)

        # A single image comes without the frame axis
        expected_ndim = 4 if is_color else 3
        if array.ndim == expected_ndim - 1:
            array = array[np.newaxis]
        if array.ndim != expected_ndim:
            raise RuntimeError(f"Cannot read pixel data of shape {array.shape}.")

        if not is_color and f.Modality in cls.HU_MODALITIES:
            # The rescaling may differ from frame to frame
            slopes, intercepts = zip(*(cls._read_rescale(f, frame) for frame in range(len(array))))
            array = np.reshape(slopes, (-1, 1, 1)) * array + np.reshape(intercepts, (-1, 1, 1))
        return np.array(array)

    @staticmethod
    def _decode(f: pydicom.Dataset) -> tuple[np.ndarray, str]:
        """Pixel data of a file, and how its samples are to be understood.

        Decoders of compressed data convert some colour spaces on the way,
        so what the file says about its samples need not hold for the
        array that comes out of it - the decoder is asked instead.
        """
        decoder = get_decoder(f.file_meta.TransferSyntaxUID)
        array, properties = decoder.as_array(f)
        interpretation = properties.get("photometric_interpretation", f.PhotometricInterpretation)
        return np.asarray(array), str(interpretation)

    @classmethod
    def _to_rgb(cls, array: np.ndarray, f: pydicom.Dataset, interpretation: str) -> np.ndarray:
        """Colour samples as 8-bit RGB, whichever way the file stores them."""
        if interpretation == "PALETTE COLOR":
            array = apply_color_lut(array, f)
            # Palettes may hold 16-bit entries, and some of them only ever
            # use the low byte of what they declare (PS3.3 C.7.9.2)
            return cls._to_8bit(array, 16 if array.max() > 255 else 8)
        if interpretation not in ("RGB", "YBR_FULL", "YBR_FULL_422"):
            raise RuntimeError(f"{interpretation} images are not supported.")
        # Colour conversion works on bytes, so the depth is dealt with first
        array = cls._to_8bit(array, int(f.get("BitsStored") or 8))
        if interpretation != "RGB":
            array = convert_color_space(array, interpretation, "RGB")
        return array

    @staticmethod
    def _to_8bit(array: np.ndarray, bits: int) -> np.ndarray:
        """Colour samples of any depth as the 8 bits a screen can show.

        The samples are scaled, not truncated: the low byte of a deep
        sample says nothing about the colour it stands for.
        """
        if bits > 8:
            array = array >> (bits - 8)
        return np.ascontiguousarray(array, dtype=np.uint8)

    @classmethod
    def _read_rescale(cls, f: pydicom.Dataset, frame: int = 0) -> tuple[float, float]:
        """Slope and intercept turning stored values into Hounsfield units."""
        group = cls._functional_group(f, frame, "PixelValueTransformationSequence") or f
        slope = group.get("RescaleSlope")
        intercept = group.get("RescaleIntercept")
        if slope is None or intercept is None:
            logger.debug("No usable rescaling of frame %d, using the values as they are.", frame)
            return 1.0, 0.0
        return float(slope), float(intercept)

    @classmethod
    def _read_window(cls, f: pydicom.Dataset) -> tuple[float, float] | None:
        """Value range (low, high) as suggested by the DICOM file itself."""
        group = cls._functional_group(f, 0, "FrameVOILUTSequence") or f
        center = cls._first_value(group.get("WindowCenter"))
        width = cls._first_value(group.get("WindowWidth"))
        if center is None or width is None or width <= 0:
            return None
        return center - width / 2, center + width / 2

    @classmethod
    def _read_pixel_spacing(cls, f: pydicom.Dataset) -> tuple[float, float] | None:
        """Physical size of a voxel (row, column) in mm, if the file says.

        Ultrasound is measured in its own regions rather than in patient
        coordinates and therefore usually says nothing here.
        """
        group = cls._functional_group(f, 0, "PixelMeasuresSequence") or f
        spacing = group.get("PixelSpacing")
        if spacing is None or len(spacing) < 2:
            logger.debug("No usable PixelSpacing, the image has no physical size.")
            return None
        return float(spacing[0]), float(spacing[1])

    @classmethod
    def _read_image_position(cls, f: pydicom.Dataset, frame: int = 0) -> tuple[float, float, float] | None:
        """Patient coordinates (x, y, z) of the centre of the first voxel.

        A multi-frame file that does not say where its individual frames
        are leaves them all at the position of the file itself.
        """
        group = cls._functional_group(f, frame, "PlanePositionSequence") or f
        position = group.get("ImagePositionPatient")
        if position is None or len(position) < 3:
            logger.debug("No usable ImagePositionPatient, the image is not placed.")
            return None
        return float(position[0]), float(position[1]), float(position[2])

    @staticmethod
    def _functional_group(f: pydicom.Dataset, frame: int, name: str) -> pydicom.Dataset | None:
        """One functional group of a single frame, if the file has any.

        Multi-frame files keep the geometry and the calibration of each
        frame in functional group sequences (PS3.3 C.7.6.16) instead of
        in the top-level attributes; what all frames share is stored once.
        """
        candidates = (("PerFrameFunctionalGroupsSequence", frame), ("SharedFunctionalGroupsSequence", 0))
        for sequence_name, index in candidates:
            sequence = f.get(sequence_name)
            if sequence is None or index >= len(sequence):
                continue
            group = sequence[index].get(name)
            if group:
                return group[0]
        return None

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
        if self.is_color:
            # Colour samples are what they are, there is nothing to window
            return 0.0, 255.0
        if self._window is not None:
            return self._window
        if self.modality in self.HU_MODALITIES:
            return DEFAULT_HU_WINDOW
        # Ignore a few percent of outlying voxels (noise, metal artifacts, ...)
        low, high = np.percentile(self._array, [1.0, 99.0])
        if high <= low:
            low, high = self._array.min(), self._array.max()
        return float(low), float(max(high, low + 1.0))

    def voxel_position(self, slice_index: int, row: float, column: float) -> tuple[float, float, float]:
        """Patient coordinates (in mm) of a voxel of the stack.

        The index is given in the order of the underlying array, i.e. the
        slice first. Rows and columns may be fractional to address a
        position inside a voxel.

        Only axis-aligned data are handled; ImageOrientationPatient is
        ignored, as is the rest of the viewer.
        """
        x, y, z = self.image_positions[slice_index]
        # PixelSpacing is (row, column) = (y, x) - the axes are swapped here
        row_spacing, column_spacing = self.pixel_spacing
        return float(x + column_spacing * column), float(y + row_spacing * row), float(z)

    @property
    def uses_hounsfield_units(self) -> bool:
        """Whether voxel values are in Hounsfield units (and not arbitrary)."""
        return self.modality in self.HU_MODALITIES

    @property
    def is_color(self) -> bool:
        """Whether a voxel is three RGB samples rather than one value."""
        return self._array.ndim == 4

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
        """Size (rows, columns) of a slice through the plane.

        Colour samples are not a dimension of the image and do not count.
        """
        shape = list(self.shape[:3])
        shape.pop(plane)
        return shape
