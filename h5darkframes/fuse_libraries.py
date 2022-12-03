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
from .image_library import ImageLibrary, ImageNotFoundError

_logger = logging.getLogger("fusion")


def _add(
    hdf5_file: h5py.File,
    controls: typing.OrderedDict[str, int],
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
    group, created = create_library._get_group(hdf5_file, controls, create)
    if group and created:
        group.create_dataset("image", data=image)
        group.attrs["camera_config"] = repr(config)
        return True
    return False


def _fuse_libraries(
    target: h5py.File,
    paths: typing.Iterable[Path],
    libs: typing.Iterable[ImageLibrary],
    params: typing.List[str],
) -> None:
    """
    Add the content of all libraries to the target
    """
    nb_added = 0
    for path, lib in zip(paths, libs):
        _logger.info(f"adding images from {path}")
        controls = lib.configs()
        for control in controls:
            # control_ has the same content as control,
            # but with ordered keys
            control_ = OrderedDict()
            for param in params:
                control_[param] = control[param]
            _logger.info("adding {control} from {path}")
            try:
                image, config = lib.get(control_)
            except ImageNotFoundError:
                _logger.error(
                    f"failed to find the image corresponding to {control} in {path}, skipping"
                )
            else:
                added = _add(target, control_, image, config)
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
    params: typing.List[str] = libs[0].controllables()
    with h5py.File(target, "a") as h5target:
        _fuse_libraries(h5target, libraries, libs, params)
        h5target.attrs["controls"] = repr([lib.params() for lib in libs])
        h5target.attrs["name"] = name
