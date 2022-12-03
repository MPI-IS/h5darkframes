import typing
import h5py
import copy
from numpy import typing as npt
from pathlib import Path
from .control_range import ControlRange
from collections import OrderedDict  # noqa: F401


def _get_closest(value: int, values: typing.List[int]) -> int:
    """
    Returns the item of values the closest to value
    (e.g. value=5, values=[1,6,10,11] : 6 is returned)
    """
    diffs = [abs(value - v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]


def _get_image(
    values: typing.List[int], hdf5_file: h5py.File, index: int = 0
) -> typing.Tuple[npt.ArrayLike, typing.Dict]:
    """
    Returns the image in the library which has been taken with
    the configuration the closest to "values".
    """

    if "image" in hdf5_file.keys():
        img = hdf5_file["image"]
        config = eval(hdf5_file.attrs["camera_config"])
        return img, config

    else:
        keys = list([int(k) for k in hdf5_file.keys()])
        best_value = _get_closest(values[index], keys)
        return _get_image(values, hdf5_file[str(best_value)], index + 1)


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

    def configs(self) -> typing.List[typing.Dict[str, int]]:
        """
        Return the list of all configurations to which a corresponding
        image is stored in the library.
        """

        def _add(controls, index, group, current, list_) -> None:
            if index == len(controls):
                list_.append(current)
                return
            for value in group.keys():
                current_ = copy.deepcopy(current)
                current_[controls[index]] = int(value)
                _add(controls, index + 1, group[value], current_, list_)

        def _add_controls(controls):
            index = 0
            group = self._hdf5_file
            _add(controls, index, group, {}, r)

        r: typing.List[typing.Dict[str, int]] = []
        if isinstance(self._controls, list):
            for controls_ in self._controls:
                controls = list(controls_.keys())
                _add_controls(controls)
        else:
            controls = list(self._controls.keys())
            _add_controls(controls)
        return r

    def controllables(self) -> typing.List[str]:
        """
        List of controllables that have been "ranged over"
        when creating the libaries
        """
        params = self.params()
        if isinstance(params, OrderedDict):
            return list(params.keys())
        return list(params[0].keys())

    def params(
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
        self, controls: typing.Dict[str, int]
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:
        """
        Returns the image in the library that was taken using
        the configuration the closest to the passed controls.

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
        image, config = _get_image(values, self._hdf5_file, index=0)
        return image, config

    def close(self) -> None:
        self._hdf5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
