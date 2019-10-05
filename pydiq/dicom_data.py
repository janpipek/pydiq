from typing import List, Tuple

import numpy as np
import pydicom


# Anatomical planes
TRANSVERSE = AXIAL = 0
FRONTAL = CORONAL = 1
MEDIAN = SAGITTAL = 2
ALLOWED_PLANES = (AXIAL, CORONAL, SAGITTAL)



class DicomData:
    ALLOWED_MODALITIES = ('CT', 'MR', 'CR', 'RT')

    def __init__(self, data, **kwargs):
        self._array = data
        self.modality = kwargs.get("modality")

    @classmethod
    def from_files(cls, files: List[str]) -> "DicomData":
        data = []
        modality = None

        for file_path in files:
            f = pydicom.read_file(file_path)
            print(f"Reading {file_path}...")

            # Get modality
            if modality:
                if modality != f.Modality:
                    raise RuntimeError("Cannot mix images from different modalities")
            elif f.Modality not in cls.ALLOWED_MODALITIES:
                raise RuntimeError(f"{f.Modality} modality not supported.")
            else:
                modality = f.Modality
            data.append(cls._read_pixel_data(f))
        return cls(np.array(data), modality=modality)

    @classmethod
    def _read_pixel_data(cls, f) -> np.ndarray:
        if f.Modality == "CT":
            data = f.RescaleSlope * f.pixel_array + f.RescaleIntercept
            return np.array(data)
        else:
            return np.array(f.pixel_array)

    @property
    def shape(self) -> Tuple[int, ...]:
        return self._array.shape

    @property
    def array(self) -> np.ndarray:
        """The underlying numpy array."""
        return self._array

    def get_slice(self, plane: str, n: int) -> np.ndarray:
        if plane not in ALLOWED_PLANES:
            raise ValueError(f"Invalid plane identificator {plane} (allowed are 0, 1, 2)")
        index = [slice(None, None, None) for i in range(3)]
        index[plane] = n
        return self._array[tuple(index)]

    def get_slice_shape(self, plane: str) -> Tuple[int, ...]:
        # TODO: 
        shape = list(self.shape)
        shape.pop(plane)
        return shape




