"""
Module for fusing several darkframe libraries into one.
"""

import typing
import h5py
import logging
from numpy import typing as npt
from pathlib import Path
from .control_range import ControlRange  # noqa: F401
from collections import OrderedDict  # noqa: F401
from . import create_library
from .get_image import ImageNotFoundError
from .image_library import ImageLibrary
from .types import Params

_logger = logging.getLogger("fusion")


def _add(
    h5: h5py.File,
    controllables: typing.Sequence[str],
    param: typing.Sequence[int],
    image: npt.ArrayLike,
    config: typing.Dict,
) -> bool:
    """
    Create the group corresponding to the controls
    and add the image in the dataset, add the configuration
    as attribute to the dataset; and returns True.
    If the group already existed, then nothing is added
    and False is returned.
    """
    create = True
    controls: typing.OrderedDict[str, int] = OrderedDict()
    for controllable, p in zip(controllables, param):
        controls[controllable] = p
    group, created = create_library._get_group(h5, controls, create)
    if group and created:
        group.create_dataset("image", data=image)
        group.attrs["camera_config"] = repr(config)
        return True
    return False


def _fuse_libraries(
    target: h5py.File,
    paths: typing.Iterable[Path],
    libs: typing.Iterable[ImageLibrary],
) -> None:
    """
    Add the content of all libraries to the target
    """
    nb_added = 0
    for path, lib in zip(paths, libs):
        _logger.info(f"adding images from {path}")
        params: Params = lib.params()
        controllables = lib.controllables()
        for param in params:
            _logger.info(f"adding {param} from {path}")
            try:
                c: typing.Dict[str, int] = {
                    controllable: value
                    for controllable, value in zip(controllables, param)
                }
                image, config = lib.get(c)
            except ImageNotFoundError:
                _logger.error(
                    f"failed to find the image corresponding to {c} in {path}, skipping"
                )
            else:
                added = _add(target, controllables, param, image, config)
                if not added:
                    _logger.debug("controls already added, skipping")
                else:
                    nb_added += 1
        _logger.info(f"added {nb_added} image(s) from {path}")


def fuse_libraries(
    name: str,
    target: Path,
    libraries: typing.Sequence[Path],
) -> None:

    # basic checks
    if not target.parents[0].is_dir():
        raise FileNotFoundError(
            f"fail to create the target file {target}, "
            f"parent folder {target.parents[0]} does not exist"
        )
    if target.is_file():
        raise ValueError(
            f"fail to create the target file {target}: " "file already exists"
        )
    for path in libraries:
        if not path.is_file():
            raise FileNotFoundError(
                f"fail to find the h5darkframes library file {path}"
            )

    # opening the libraries to fuse
    libs = [ImageLibrary(l_) for l_ in libraries]

    # checking all libraries are based on the same
    # controllables
    controllables: typing.List[typing.Set[str]]
    controllables = [set(lib.controllables()) for lib in libs]
    for index, (c1, c2) in enumerate(zip(controllables, controllables[1:])):
        if not c1 == c2:
            raise ValueError(
                f"can not fuse libraries {libraries[index]} and {libraries[index+1]}: "
                f"not based on the same controllables ({c1} and {c2})"
            )

    # params is the list of controls used, in order (it matters)
    # (ImageLibrary.params returns an OrderedDict)
    with h5py.File(target, "a") as h5target:
        _fuse_libraries(h5target, libraries, libs)
        h5target.attrs["controls"] = repr([lib.ranges() for lib in libs])
        h5target.attrs["name"] = name
