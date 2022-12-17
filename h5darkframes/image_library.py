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

    def __init__(self, hdf5_path: Path) -> None:

        # path to the library file darkframes.hdf5
        self._path = hdf5_path

        # handle to the content of the file
        self._h5 = h5py.File(hdf5_path, "r")

        # List of control ranges used to create the file.
        self._ranges: Ranges = eval(self._h5.attrs["controls"])

        # list of controllables covered by the library
        self._controllables: Controllables
        if isinstance(self._ranges, OrderedDict):
            self._controllables = tuple(ranges.keys())
        else:
            self._controllables = tuple(ranges[0].keys())

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

    def add(
            self,
            controls: typing.Union[typing.Tuple[int, ...], typing.Dict[str, int]],
            img: npt.ArrayLike,
            camera_config: typing.Dict,
            overwrite: bool
    )->bool:

        if isinstance(controls, dict):
            values = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            values = controls

        return h5.add(self._h5, values, img, camera_config, overwrite)
            
        
    def rm(
            self,
            controls: typing.Union[typing.Tuple[int, ...], typing.Dict[str, int]],
    )->typing.Optional[typing.Tuple[npt.ArrayLike, typing.Dict]]:
        
        if isinstance(controls, dict):
            values = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
        else:
            values = controls

        return h5.rm(self._h5,values)
            
        
    def get(
        self,
        controls: typing.Union[typing.Tuple[int, ...], typing.Dict[str, int]],
        get_type: GetType,
        nparray: bool = False,
    ) -> typing.Tuple[npt.ArrayLike, typing.Dict]:

        if isinstance(controls, dict):
            values = tuple(
                [controls[controllable] for controllable in self._controllables]
            )
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
