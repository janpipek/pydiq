import numpy as np
import dicom

# Anatomical planes
TRANSVERSE = AXIAL = 0
FRONTAL = CORONAL = 1
MEDIAN = SAGITTAL = 2
ALLOWED_PLANES = (AXIAL, CORONAL, SAGITTAL)


class DicomData(object):
    ALLOWED_MODALITIES = ('CT', 'MR', 'CR', 'RT')

    def __init__(self, data, **kwargs):
        self._array = data
        self.modality = kwargs.get("modality")

    @classmethod
    def from_files(cls, files):
        data = []
        modality = None

        for file_path in files:
            f = dicom.read_file(file_path)
            print("Reading %s..." % file_path)

            # Get modality
            if modality:
                if modality != f.Modality:
                    raise RuntimeError("Cannot mix images from different modalities")
            elif f.Modality not in cls.ALLOWED_MODALITIES:
                raise RuntimeError("%s modality not supported" % f.Modality)
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
        """The underlying numpy array."""
        return self._array

    def get_slice(self, plane, n):
        if plane not in ALLOWED_PLANES:
            raise ValueError("Invalid plane identificator (allowed are 0,1,2)")
        index = [slice(None, None, None) for i in range(3)]
        index[plane] = n
        return self._array[index]

    def get_slice_shape(self, plane):
        # TODO: 
        shape = list(self.shape)
        shape.pop(plane)
        return shape




