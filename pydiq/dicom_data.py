import numpy as np
import dicom

class DicomData(object):
    ALLOWED_MODALITIES = ('CT', 'MRI', 'CR')

    def __init__(self, data, **kwargs):
        self._array = data
        self.modality = kwargs.get("modality")

    @classmethod
    def from_files(cls, files):
        data = []
        modality = None

        for file_path in files:
            f = dicom.read_file(file_path)

            # Get modality
            if modality:
                if modality != f.Modality:
                    raise StandardError("Cannot mix images from different modalities")
            elif f.Modality not in cls.ALLOWED_MODALITIES:
                raise StandardError("%s modality not supported" % modality)
            else:
                modality = f.Modality
            data.append(cls._read_pixel_data(f))
        return cls(np.array(data), modality=modality)

    @classmethod
    def _read_pixel_data(cls, f):
        if f.Modality == "CT":
            data = f.RescaleSlope * f.pixel_array + f.RescaleIntercept
            return np.array(data)
        else:
            return np.array(f.pixel_array)

    @property
    def shape(self):
        return self._array.shape

    @property
    def array(self):
        """Numpy array."""
        return self._array


