import typing
import h5py
import numpy as np
from numpy import typing as npt
from .types import Param, ParamImage


def get_group(
    h5: h5py.File, param: Param, create: bool
) -> typing.Tuple[typing.Optional[h5py.File], bool]:
    """
    Returns the group hosting the darkframe dataset if the hdf5 file
    contains an entry for the provided parameters, None, otherwise.
    If create is True, the group will be created if it does not exists.
    The boolean indicating whether or not the group was created
    is also returned.
    """
    group = h5
    created = False
    for p in param:
        try:
            group = group[str(p)]
        except KeyError:
            if create:
                group = group.require_group(str(p))
                created = True
            else:
                return None, False
    return group, created


def add(
    h5: h5py.File,
    param: Param,
    img: npt.ArrayLike,
    camera_config: typing.Dict,
    overwrite: bool,
) -> bool:
    """
    Write the image and the camera configuration to the
    file. If overwrite is False and there is already an image
    corresponding to the parameters, then the data is not
    writen in the file and False is returned.
    """

    create = True
    group, created = get_group(h5, param, create)

    if not created and not overwrite:
        return False
    if not group:
        return False

    group.create_dataset("image", data=img)
    group.attrs["camera_config"] = repr(camera_config)

    return True


def rm(h5: h5py.File, param: Param) -> typing.Optional[ParamImage]:

    groups = [h5]
    group = h5

    for p in param:
        try:
            group = group[str(p)]
        except KeyError:
            return None
        groups.append(group)

    try:
        img_ = group["image"]
    except KeyError:
        return None

    img = np.zeros(img_.shape, img_.dtype)
    img_.read_direct(img)

    try:
        config = eval(group.attrs["camera_config"])
    except KeyError:
        return None

    del group["image"]
    del group.attrs["camera_config"]

    groups.reverse()
    for group in groups:
        if not list(group.keys()):
            del group.parent[group.name]

    return param, img, config
