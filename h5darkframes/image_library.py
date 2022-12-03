import typing
import h5py
import copy
import numpy as np
from numpy import typing as npt
from pathlib import Path
from .control_range import ControlRange
from collections import OrderedDict  # noqa: F401


class ImageNotFoundError(Exception):
    pass


class ImageStats:
    def __init__(self, image: npt.ArrayLike) -> None:
        self.shape: typing.Tuple[int, ...] = image.shape  # type: ignore
        self.min = np.min(image)
        self.max = np.max(image)
        self.avg = np.average(image)  # type: ignore
        self.std = np.std(image)  # type: ignore

    def pretty(self) -> typing.List[str]:
        return [
            str(self.shape),
            str(self.min),
            str(self.max),
            str("%.2f" % self.avg),
            str("%.2f" % self.std),
        ]

    def __str__(self):
        return str(
            f"shape: {self.shape} min: {self.min} max: {self.max} "
            f"average: {'%.2f' % self.avg} std: {'%.2f' % self.std}"
        )


def _get_closest(value: int, values: typing.List[int]) -> int:
    """
    Returns the item of values the closest to value
    (e.g. value=5, values=[1,6,10,11] : 6 is returned)
    """
    diffs = [abs(value - v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]


def _get_image(
    values: typing.List[int],
    hdf5_file: h5py.File,
    index: int = 0,
    nparray: bool = False,
) -> typing.Tuple[npt.ArrayLike, typing.Dict]:
    """
    Returns the image in the library which has been taken with
    the configuration the closest to "values".
    """

    if "image" in hdf5_file.keys():
        img = hdf5_file["image"]
        config = eval(hdf5_file.attrs["camera_config"])
        if not nparray:
            return img, config
        else:
            # converting the h5py dataset to numpy array
            array = np.zeros(img.shape, img.dtype)
            img.read_direct(array)
            return array, config
    else:
        keys = list([int(k) for k in hdf5_file.keys()])
        if index >= len(values):
            raise ImageNotFoundError()
        best_value = _get_closest(values[index], keys)
        return _get_image(
            values, hdf5_file[str(best_value)], index + 1, nparray=nparray
        )


class ImageLibrary:
    """
    Object for reading an hdf5 file that must have been generated
    using the 'create_hdf5' method of this module.
    Allows to access images in the library.
    """

    def __init__(self, hdf5_path: Path) -> None:
        self._path = hdf5_path
        self._hdf5_file = h5py.File(hdf5_path, "r")
        self._controls = eval(self._hdf5_file.attrs["controls"])

    def configs(self) -> typing.List[typing.OrderedDict[str, int]]:
        """
        Return the list of all configurations to which a corresponding
        image is stored in the library.
        """

        def _append_configs(
            controllables: typing.List[str],
            h5: h5py.File,
            index: int,
            current: typing.OrderedDict[str, int],
            c: typing.List[typing.OrderedDict[str, int]],
        ):
            if index >= len(controllables):
                c.append(current)
                return
            for key in sorted(h5.keys()):
                current_ = copy.deepcopy(current)
                current_[controllables[index]] = int(key)
                _append_configs(controllables, h5[key], index + 1, current_, c)

        controllables: typing.List[str] = self.controllables()
        h5: h5py.File = self._hdf5_file
        index: int = 0
        current: typing.OrderedDict[str, int] = OrderedDict()
        c: typing.List[typing.OrderedDict[str, int]] = []

        _append_configs(controllables, h5, index, current, c)

        return c

    def nb_pics(self) -> int:
        """
        Returns the number of darkframes
        contained by the library.
        """
        configs = self.configs()
        found = 0
        for config in configs:
            try:
                self.get(config)
                found += 1
            except ImageNotFoundError:
                pass
        return found

    def controllables(self) -> typing.List[str]:
        """
        List of controllables that have been "ranged over"
        when creating the libaries
        """
        params = self.ranges()
        if isinstance(params, OrderedDict):
            return list(params.keys())
        return list(params[0].keys())

    def ranges(
        self,
    ) -> typing.Union[
        typing.List[typing.OrderedDict[str, ControlRange]],
        typing.OrderedDict[str, ControlRange],
    ]:
        """
        Returns the range of values that have been used to generate
        this file.
        """
        return eval(self._hdf5_file.attrs["controls"])

    def name(self) -> str:
        """
        Returns the name of the library, which is an arbitrary
        string passed as argument by the user when creating the
        library.
        """
        try:
            return self._hdf5_file.attrs["name"]
        except KeyError:
            return "(not named)"

    def get(
        self, controls: typing.Dict[str, int], nparray: bool = False
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:
        """
        Returns the image in the library that was taken using
        the configuration the closest to the passed controls.

        If not nparray, the image will be a h5py data instance (can not be accessed once the file is closed). Otherwise
        the image will be a numpy array (hard copy of the h5py dataset)

        Arguments
        ---------
        controls:
          keys of controls are expected to the the same as
          the keys of the dictionary returned by the method
          'params' of this class

        Returns
        -------
        Image of the library and its related camera configuration
        """

        for control in controls:
            if control not in self.controllables():
                slist = ", ".join(self._controls)
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the control {control} is not supported (supported: {slist})"
                )

        for control in self.controllables():
            if control not in controls:
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the value for the control {control} needs to be specified"
                )

        values = list(controls.values())
        image: npt.ArrayLike
        config: typing.Dict
        image, config = _get_image(values, self._hdf5_file, index=0, nparray=nparray)
        return image, config

    def close(self) -> None:
        self._hdf5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
