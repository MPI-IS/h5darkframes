import typing
import h5py
import copy
import numpy as np
from numpy import typing as npt
from pathlib import Path
from collections import OrderedDict  # noqa: F401
from .types import Controllables, Ranges, Param, Params, ParamImage
from .get_image import get_image
from .neighbors import (
    get_neighbors,
    closest_neighbors,
    average_neighbors,
    interpolation_neighbors,
)
from .control_range import ControlRange  # noqa: F401
from . import h5


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
            if "image" in h5.keys():
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

    def __init__(self, hdf5_path: Path, edit: bool = False) -> None:

        # path to the library file darkframes.hdf5
        self._path = hdf5_path

        # handle to the content of the file
        self._edit = edit
        if not edit:
            self._h5 = h5py.File(hdf5_path, "r")
        else:
            self._h5 = h5py.File(hdf5_path, "a")

        # List of control ranges used to create the file.
        self._ranges: Ranges = eval(self._h5.attrs["controls"])

        # list of controllables covered by the library
        self._controllables: Controllables = _get_controllables(self._ranges)

        # list of parameters for which a darframe is stored
        self._params: Params = _get_params(self._h5, self._controllables)

        # same as above, but as a matrix (row as params)
        self._params_points: npt.ArrayLike = np.array(self._params)

        # min and max values for each controllables
        self._min_params: typing.Tuple[int, ...] = tuple(
            self._params_points.min(axis=0)
        )
        self._max_params: typing.Tuple[int, ...] = tuple(
            self._params_points.max(axis=0)
        )

    def add(
        self,
        param: Param,
        img: npt.ArrayLike,
        camera_config: typing.Dict,
        overwrite: bool,
    ) -> bool:
        if not self._edit:
            raise RuntimeError(
                "can not add image to the darkframes library: it has not "
                "been open in editable mode"
            )
        r = h5.add(self._h5, param, img, camera_config, overwrite)
        if r:
            self._params.append(param)
        return r

    def rm(self, param: Param) -> typing.Optional[ParamImage]:
        if not self._edit:
            raise RuntimeError(
                "can not delete image to the darkframes library: it has not "
                "been open in editable mode"
            )
        r = h5.rm(self._h5, param)
        if r is not None:
            self._params.remove(param)
        return r

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
        controls: typing.Union[Param, typing.Dict[str, int]],
        nparray: bool = True,
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:

        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        closest = False
        return get_image(params, self._h5, nparray, closest)

    def get_closest(
        self,
        controls: typing.Union[Param, typing.Dict[str, int]],
    ) -> Param:
        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        return closest_neighbors(
            self._params, self._min_params, self._max_params, params, nb_closest=1
        )[0]

    def get_neighbors(
        self, controls: typing.Union[Param, typing.Dict[str, int]]
    ) -> Params:

        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        neighbors: Params = get_neighbors(
            self._params, self._min_params, self._max_params, params
        )

        return neighbors

    def get_interpolation_neighbors(
        self, controls: typing.Union[Param, typing.Dict[str, int]], fixed_index: int = 1
    ) -> Params:
        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        neighbors: Params = interpolation_neighbors(self._params, params, fixed_index)

        return neighbors

    def generate_darkframe(
        self, controls: typing.Union[Param, typing.Dict[str, int]], neighbors: Params
    ) -> npt.ArrayLike:

        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        nparray = True
        neighbor_images = {
            neighbor: self.get(neighbor, nparray) for neighbor in neighbors
        }
        return average_neighbors(
            params, self._min_params, self._max_params, neighbor_images
        )

    def close(self) -> None:
        self._h5.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
