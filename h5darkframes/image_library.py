import typing
import h5py
import copy
import numpy as np
from enum import Enum
from numpy import typing as npt
from pathlib import Path
from collections import OrderedDict  # noqa: F401
from .types import Controllables, Ranges, Params, ParamImages
from .get_image import get_image
from .neighbors import get_neighbors, average_neighbors
from .control_range import ControlRange  # noqa: F401


class GetType(Enum):
    exact = 1
    closest = 2
    neighbors = 3


def _get_controllables(ranges: Ranges) -> typing.Tuple[str, ...]:
    """
    List of controllables that have been "ranged over"
    when creating the libaries
    """
    if isinstance(ranges, OrderedDict):
        return tuple(ranges.keys())
    return tuple(ranges[0].keys())


def _get_params(
    h5: h5py.File,
    controllables: Controllables,
) -> Params:
    """
    Return the list of all configurations to which a corresponding
    image is stored in the library.
    """

    def _append_configs(
        controllables: Controllables,
        h5: h5py.File,
        index: int,
        current: typing.List[int],
        c: Params,
    ):
        if index >= len(controllables):
            c.append(tuple(current))
            return
        for key in sorted(h5.keys()):
            current_ = copy.deepcopy(current)
            current_.append(int(key))
            _append_configs(controllables, h5[key], index + 1, current_, c)

    index: int = 0
    current: typing.List[int] = []
    c: Params = []
    _append_configs(controllables, h5, index, current, c)

    return c


class ImageLibrary:
    """
    Object for reading an hdf5 file that must have been generated
    using the 'create_hdf5' method of this module.
    Allows to access images in the library.
    """

    def __init__(self, hdf5_path: Path) -> None:

        # path to the library file darkframes.hdf5
        self._path = hdf5_path

        # handle to the content of the file
        self._h5 = h5py.File(hdf5_path, "r")

        # List of control ranges used to create the file.
        self._ranges: Ranges = eval(self._h5.attrs["controls"])

        # list of controllables covered by the library
        self._controllables: Controllables = _get_controllables(self._ranges)

        # list of parameters for which a darframe is stored
        self._params: Params = _get_params(self._h5, self._controllables)

        # same as above, but as a matrix (row as params)
        self._params_points: npt.ArrayLike = np.array(self._params)

        # min and max values for each controllables
        self._min_values: typing.Tuple[int, ...] = tuple(
            self._params_points.min(axis=0)
        )
        self._max_values: typing.Tuple[int, ...] = tuple(
            self._params_points.max(axis=0)
        )

    def params(self) -> Params:
        return self._params

    def nb_pics(self) -> int:
        """
        Returns the number of darkframes
        contained by the library.
        """
        return len(self._params)

    def controllables(self) -> typing.Tuple[str, ...]:
        return self._controllables

    def ranges(self) -> Ranges:
        """
        Returns the range of values that have been used to generate
        this file.
        """
        return self._ranges

    def name(self) -> str:
        """
        Returns the name of the library, which is an arbitrary
        string passed as argument by the user when creating the
        library.
        """
        try:
            return self._h5.attrs["name"]
        except KeyError:
            return "(not named)"

    def get(
        self,
        controls: typing.Union[ typing.Tuple[int,...] , typing.Dict[str, int] ],
        get_type: GetType,
        nparray: bool = False
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:

        if isinstance(controls,dict):
            values = tuple([controls[controllable] for controllable in self._controllables])
        else:
            values = controls
            
        if get_type == GetType.exact:
            closest = False
            return get_image(values, self._h5, nparray, closest)

        elif get_type == GetType.closest:
            closest = True
            return get_image(values, self._h5, nparray, closest)

        elif get_type == GetType.neighbors:
            neighbors: ParamImages = get_neighbors(self._h5, values)
            if not neighbors:
                return self.get(controls, GetType.closest, nparray)
            else:
                return (
                    average_neighbors(
                        values, self._min_values, self._max_values, neighbors
                    ),
                    {},
                )

        raise ValueError(
            "ImageLibrary get method called with unsupported " f"GetType: {get_type}"
        )

    def close(self) -> None:
        self._h5.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
