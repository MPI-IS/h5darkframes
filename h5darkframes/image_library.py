import typing
import h5py
import copy
import numpy as np
from enum import Enum
from numpy import typing as npt
from pathlib import Path
from collections import OrderedDict  # noqa: F401
from .types import Controllables, Ranges, Param, Params, ParamImage
from .get_image import get_image
from .neighbors import get_neighbors, average_neighbors
from .control_range import ControlRange  # noqa: F401
from . import h5


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


class DarkframeError(Exception):
    def __init__(
        self,
        img: npt.NDArray,
        dtype=None,
        shape: typing.Optional[typing.Tuple[int, int]] = None,
    ):
        if dtype is not None:
            self._error = str(
                f"darkframe expects an image of type {dtype}, "
                f"got {img.dtype} instead"  # type: ignore
            )
        elif shape is not None:
            self._error = str(
                f"darkframe expects an image of shape {shape}, "
                f"got {img.shape} instead"  # type: ignore
            )
        else:
            self._error = "darkframe substraction error"

    def __str__(self) -> str:
        return self._error


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
        controls: typing.Union[typing.Tuple[int, ...], typing.Dict[str, int]],
        get_type: GetType,
        nparray: bool = False,
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:

        if isinstance(controls, dict):
            params = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            params = controls

        if get_type == GetType.exact:
            closest = False
            return get_image(params, self._h5, nparray, closest)

        elif get_type == GetType.closest:
            closest = True
            return get_image(params, self._h5, nparray, closest)

        elif get_type == GetType.neighbors:
            neighbors: Params = get_neighbors(
                self._h5, params, self._min_params, self._max_params
            )
            if not neighbors:
                return self.get(controls, GetType.closest, nparray)
            else:
                neighbor_images = {
                    neighbor: self.get(neighbor, GetType.closest, nparray)
                    for neighbor in neighbors
                }
                return (
                    average_neighbors(
                        params, self._min_params, self._max_params, neighbor_images
                    ),
                    {},
                )

        raise ValueError(
            "ImageLibrary get method called with unsupported " f"GetType: {get_type}"
        )

    def substract(
        self,
        img: npt.NDArray,
        config: typing.Dict[str, int],
        conversion: typing.Dict[str, typing.Tuple[str, typing.Callable[[int], int]]] = {
            "TargetTemp": ("Temperature", lambda t: int(t / 10.0 + 0.5))
        },
    ):

        # for asi-zwo camera: the darkframes were created by ranging over target temperature,
        # but for retrieving the desired darkframe, the temperature (and not the target temperature)
        # has to be used.
        for origin, target in conversion.items():
            if origin in config and target[0] in config:
                config = copy.deepcopy(config)
                config[origin] = target[1](config[target[0]])

        # checking we have in the configuration of the image the information
        # required to retrieve the darkframe
        controllables = self.controllables()
        for controllable in controllables:
            if controllable not in config:
                raise ValueError(
                    f"Can not substract darkframes: the library {self.name()} requires "
                    f"value for the controllable {controllable}"
                )

        # getting a suitable darkframe
        darkframe, _ = self.get(config, GetType.neighbors, nparray=True)

        # checking the darkframe is of suitable type/shape
        if not darkframe.dtype == img.dtype:  # type: ignore
            raise DarkframeError(img, dtype=darkframe.dtype)  # type: ignore
        if not darkframe.shape == img.shape:  # type: ignore
            raise DarkframeError(img, shape=darkframe.shape)  # type: ignore

        # substracting
        im64 = img.astype(np.uint64)
        dark64 = darkframe.astype(np.uint64)  # type: ignore
        sub64 = im64 - dark64
        sub64[sub64 < 0] = 0

        # returning
        return sub64.astype(img.dtype)

    def close(self) -> None:
        self._h5.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
