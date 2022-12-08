import typing
import h5py
from numpy import typing as npt
import numpy as np


class ImageNotFoundError(Exception):
    pass


def _get_closest(value: int, values: typing.List[int]) -> int:
    """
    Returns the item of values the closest to value
    (e.g. value=5, values=[1,6,10,11] : 6 is returned)
    """
    diffs = [abs(value - v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]


def get_image(
    values: typing.Tuple[int, ...], h5: h5py.File, nparray: bool, closest: bool
) -> typing.Tuple[npt.ArrayLike, typing.Dict]:
    def _retrieve(
        values: typing.Tuple[int, ...],
        hdf5_file: h5py.File,
        nparray: bool,
        closest: bool,
        index: int,
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:

        if "image" in hdf5_file.keys():

            img = hdf5_file["image"]
            try:
                config = eval(hdf5_file.attrs["camera_config"])
            except AttributeError:
                config = {}
            if not nparray:
                return img, config
            else:
                # converting the h5py dataset to numpy array
                array = np.zeros(img.shape, img.dtype)
                img.read_direct(array)
                return array, config

        else:
            if index >= len(values):
                raise ImageNotFoundError()
            keys = list([int(k) for k in hdf5_file.keys()])
            value: int
            if values[index] not in keys:
                if closest:
                    value = _get_closest(values[index], keys)
                else:
                    raise ImageNotFoundError()
            else:
                value = values[index]
            return _retrieve(values, hdf5_file[str(value)], nparray, closest, index + 1)

    return _retrieve(values, h5, nparray, closest, 0)
